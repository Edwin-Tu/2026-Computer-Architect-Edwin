#!/usr/bin/env python3
"""Maintenance regressions; replay is not a source rebuild or native C run."""
import datetime
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
import re
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("check_cp2.py")
spec = importlib.util.spec_from_file_location("cp2_review_module", SCRIPT)
cp2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp2)
VALIDATION = Path(os.environ.get("CP2_VALIDATION_ROOT", str(cp2.ROOT / "build" / ("flow_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])))).resolve()

class SavedCode:
    static_metrics = cp2.ELF32.static_metrics
    def __init__(self, codes=None, symbols=None):
        self.codes = codes or {}
        self.symbols = symbols or {"test": (0, 4 * len(self.codes))}
    def read_u32(self, addr):
        if addr % 4 or addr not in self.codes:
            raise ValueError(f"PC outside aligned executable fixture: {addr}")
        return self.codes[addr]

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.out = VALIDATION / (self._testMethodName + "_" + uuid.uuid4().hex[:8])
        self.out.mkdir(parents=True, exist_ok=False)
        self.original_output = cp2.OUTPUT
        cp2.OUTPUT = self.out
    def tearDown(self):
        cp2.OUTPUT = self.original_output

    def test_source_paths_exist(self):
        hashes = cp2.validate_sources()
        self.assertEqual(len(hashes), 6)
        self.assertEqual(len(cp2.CP1_CASES), 14)
        self.assertEqual(len(cp2.prepare_cases()), 5199)

    def test_missing_source_is_failure(self):
        with patch.object(cp2, "ROOT", self.out):
            with self.assertRaises(FileNotFoundError):
                cp2.validate_sources()

    def test_native_arguments_and_summary_contract(self):
        stdout = "\n".join("[PASS] " + str(i) for i in range(14)) + "\nResult: 14/14 tests passed.\n"
        completed = subprocess.CompletedProcess([], 0, stdout, "")
        with patch.object(cp2, "run_command", return_value=completed) as mocked:
            self.assertEqual(cp2.native_check("test-cc"), "14/14 native C tests passed")
        argv = mocked.call_args_list[1].args[0]
        self.assertIn(str(cp2.ROOT / "tests/test_min.c"), argv)
        self.assertIn(str(cp2.ROOT / "c_baseline/min.c"), argv)
        self.assertEqual(argv[argv.index("-I") + 1], str(cp2.ROOT / "c_baseline"))

    def test_native_crlf_summary_is_accepted(self):
        stdout = "\r\n".join("[PASS] " + str(i) for i in range(14)) + "\r\nResult: 14/14 tests passed.\r\n"
        completed = subprocess.CompletedProcess([], 0, stdout, "")
        with patch.object(cp2, "run_command", return_value=completed):
            self.assertEqual(cp2.native_check("test-cc"), "14/14 native C tests passed")

    def test_native_crlf_failure_is_not_accepted(self):
        stdout = "\r\n".join("[PASS] " + str(i) for i in range(14)) + "\r\n[FAIL] 15\r\nResult: 14/14 tests passed.\r\n"
        completed = subprocess.CompletedProcess([], 0, stdout, "")
        with patch.object(cp2, "run_command", return_value=completed):
            with self.assertRaises(AssertionError): cp2.native_check("test-cc")

    def test_native_missing_tool_is_not_pass(self):
        with patch.object(cp2.shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError): cp2.native_check()

    def test_native_wrong_summary_is_failure(self):
        completed = subprocess.CompletedProcess([], 0, "Result: 14/14 tests passed.\n", "")
        with patch.object(cp2, "run_command", return_value=completed):
            with self.assertRaises(AssertionError): cp2.native_check("test-cc")

    def test_command_nonzero_is_failure_and_logged(self):
        with self.assertRaises(RuntimeError):
            cp2.run_command([sys.executable, "-B", "-c", "raise SystemExit(7)"], "expected_failure.log")
        self.assertIn("exit_code=7", (self.out / "expected_failure.log").read_text(encoding="utf-8"))

    def test_abi_clobber_is_rejected(self):
        code = SavedCode({0: 0x00100413, 4: 0x00008067})  # addi s0,zero,1; ret
        with self.assertRaisesRegex(AssertionError, "ABI"):
            cp2.run_function(code, "test", 1, 2)

    def test_return_via_temporary_register_is_accepted(self):
        code = SavedCode({0: 0x00008293, 4: 0x00028067})  # mv t0,ra; jalr zero,0(t0)
        result = cp2.run_function(code, "test", 1, 2)
        self.assertEqual(result["result"], 1)
        self.assertEqual(result["instructions"], 2)

    def test_branch_outside_executable_data_is_rejected(self):
        code = SavedCode({0: 0x0080006F})  # jal zero,+8 outside fixture function
        with self.assertRaisesRegex(ValueError, "outside"):
            cp2.run_function(code, "test", 1, 2)

    def test_existing_output_is_never_overwritten(self):
        marker = self.out / "marker.txt"
        marker.write_text("keep", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--output-dir", str(self.out)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.out / "measurements.json").exists())

    def test_missing_riscv_compiler_cli_is_failure(self):
        run = self.out / "new_run"
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--skip-native", "--compiler",
                                 str(self.out / "missing-riscv-gcc"), "--output-dir", str(run)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertNotEqual(result.returncode, 0)
        status = json.loads((run / "run_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "failed")
        self.assertIn("NOT PASS", status["native_test"])
        self.assertFalse((run / "measurements.json").exists())

    def test_return_with_caller_saved_link_register_is_accepted(self):
        code = SavedCode({0: 0x000082E7})  # jalr t0,0(ra): caller-saved link is legal
        self.assertEqual(cp2.run_function(code, "test", 1, 2)["result"], 1)

    def test_callee_saved_register_restored_is_accepted(self):
        code = SavedCode({0: 0x00040313, 4: 0x00100413, 8: 0x00030413, 12: 0x00008067})
        # save s0 in t1; change s0; restore s0; ret (test fixture only, not MIN source)
        self.assertEqual(cp2.run_function(code, "test", 1, 2)["result"], 1)

    def test_jump_to_executable_helper_is_accepted(self):
        code = SavedCode({0: 0x0080006F, 8: 0x00008067}, {"test": (0, 4), "helper": (8, 4)})
        self.assertEqual(cp2.run_function(code, "test", 1, 2)["instructions"], 2)

    def test_compiler_success_without_new_elf_is_rejected(self):
        completed = subprocess.CompletedProcess([], 0, "", "")
        with patch.object(cp2, "run_command", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "without creating"):
                cp2.compile_rv32("test-compiler")

    def test_command_log_is_not_overwritten(self):
        marker = self.out / "existing.log"
        marker.write_text("prior log", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            cp2.run_command([sys.executable, "-B", "-c", "raise SystemExit(0)"], "existing.log")
        self.assertEqual(marker.read_text(encoding="utf-8"), "prior log")

    def test_native_failed_process_is_not_pass(self):
        with patch.object(cp2, "run_command", side_effect=RuntimeError("expected native compile failure")):
            with self.assertRaises(RuntimeError): cp2.native_check("test-cc")

    def test_sp_clobber_is_rejected(self):
        code = SavedCode({0: 0xFF010113, 4: 0x00008067})  # addi sp,sp,-16; ret
        with self.assertRaisesRegex(AssertionError, "ABI"):
            cp2.run_function(code, "test", 1, 2)

    def test_truncated_elf_is_clear_failure(self):
        fixture = self.out / "truncated_fixture_NOT_historical.elf"
        fixture.write_bytes(b"\x7fELF")
        with self.assertRaises(ValueError): cp2.ELF32(fixture)

    def test_saved_machine_code_replay(self):
        dis_path = cp2.ROOT / "references/disassembly_gcc16.txt"
        text = dis_path.read_text(encoding="utf-8")
        codes = {int(a, 16): int(c, 16) for a,c in
                 re.findall(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})", text, re.MULTILINE)}
        symbols = {"min_s32": (0x10000, 16), "min_branch": (0x10010, 12),
                   "min_branchless": (0x1001c, 24)}
        result = cp2.measure(SavedCode(codes, symbols))
        historical = json.loads((cp2.ROOT / "references/measurements.json").read_text(encoding="utf-8"))
        for key, value in result.items(): self.assertEqual(value, historical[key], key)
        record = {"kind": "saved_machine_code_replay_NOT_source_rebuild", "interpreter": "v1.2.1",
                  "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "python": sys.version, "platform": platform.platform(), "source_version": "main@e084ba0-plus-cp2-maintenance",
                  "disassembly_sha256": hashlib.sha256(dis_path.read_bytes()).hexdigest(),
                  "script_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
                  "native_c_test": "NOT RUN by this replay", "metrics_match_historical_json": True,
                  "result": result}
        (self.out / "saved_code_replay.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    unittest.main(verbosity=2)
