from benchmark.clock_model import breakeven_ratio, cpu_time_ratio, cycles_per_element, mix_mac, mix_standard


def main():
    print("| mul CPI | MAC CPI | 標準 cycles/元素 | MAC cycles/元素 | 損益平衡 T 比 | T 比 1.0 時 CPU Time 比 |")
    print("|---:|---:|---:|---:|---:|---:|")
    for mul_cpi in (1, 3, 5):
        for mac_cpi in (1, 3):
            std = cycles_per_element(mix_standard(mul_cpi))
            mac = cycles_per_element(mix_mac(mac_cpi))
            print(f"| {mul_cpi} | {mac_cpi} | {std} | {mac} | {breakeven_ratio(mul_cpi, mac_cpi):.3f} | "
                  f"{cpu_time_ratio(mul_cpi, mac_cpi, 1.0):.3f} |")


if __name__ == "__main__":
    main()
