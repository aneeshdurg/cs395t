import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def parse_diskann_results(file_path):
    data = []
    with open(file_path, "r") as f:
        content = f.readlines()
        lines = content[2:]
        for l in lines:
            _, _, _, p50_latency_us, p999_latency_us, recall = l.split()
            data.append(
                {
                    "p50_latency_us": p50_latency_us,
                    "p999_latency_us": p999_latency_us,
                    "recall": recall,
                }
            )
    return {
        "file": file_path,
        "data": data,
    }


def parse_perf_results(file_path):
    data = {"dtlb_misses": 0, "page_faults": 0}
    with open(file_path, "r") as f:
        for line in f:
            if "page-faults" in line:
                faults_str = re.search(r"([\d,]+)\s+page-faults", line).group(1)
                data["page_faults"] = int(faults_str.replace(",", ""))
            if "dTLB-load-misses" in line:
                misses_str = re.search(r"([\d,]+)\s+dTLB-load-misses", line).group(1)
                data["dtlb_misses"] = int(misses_str.replace(",", ""))
    return data


def main():
    results_dir = "test_results_glibc/diskann"
    settings = ["never", "madvise", "always"]
    print("--- Generating plots ---")
    data = []
    for setting in settings:
        diskann_file = os.path.join(results_dir, f"diskann_results_{setting}.txt")
        perf_file = os.path.join(results_dir, f"diskann_perf_results_{setting}.txt")
        if not (os.path.exists(diskann_file) and os.path.exists(perf_file)):
            print(f"Warning: Result files for setting '{setting}' not found. Skipping.")
            continue
        result = {"setting": setting}
        result.update(parse_diskann_results(diskann_file))
        result.update(parse_perf_results(perf_file))
        data.append(result)
    if not data:
        print("Error: No data was parsed. Please check the 'test_results' directory.")
        return

    df = pd.DataFrame(data)
    df.set_index("setting", inplace=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    # Plot 3: dTLB Load Misses
    fig3, ax3 = plt.subplots()
    df["dtlb_misses"].plot(
        kind="bar", ax=ax3, color=["#d9534f", "#5cb85c", "#5bc0de"], rot=0
    )
    ax3.set_title("dTLB Load Misses", fontsize=14, fontweight="bold")
    ax3.set_ylabel("Misses (Log Scale)")
    ax3.set_xlabel("")
    ax3.set_yscale("log")  # Use log scale due to huge difference in misses for some
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    for container in ax3.containers:
        ax3.bar_label(container, labels=[f"{v:,.0f}" for v in container.datavalues])
    fig3.tight_layout()
    plot3_path = os.path.join(results_dir, "plot_dtlb_misses.png")
    fig3.savefig(plot3_path)
    print(f"Saved dTLB misses plot to: {plot3_path}")
    # Plot 4: dTLB Load Misses
    fig4, ax4 = plt.subplots()
    df["page_faults"].plot(
        kind="bar", ax=ax4, color=["#d9534f", "#5cb85c", "#5bc0de"], rot=0
    )
    ax4.set_title("Page Faults", fontsize=14, fontweight="bold")
    ax4.set_ylabel("Faults (Log Scale)")
    ax4.set_xlabel("")
    ax4.set_yscale("log")  # Use log scale due to huge difference in misses for some
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    for container in ax4.containers:
        ax4.bar_label(container, labels=[f"{v:,.0f}" for v in container.datavalues])
    fig4.tight_layout()
    plot4_path = os.path.join(results_dir, "plot_page_faults.png")
    fig4.savefig(plot4_path)
    print(f"Saved page faults plot to: {plot4_path}")
    plt.close("all")  # Close all figures before the next loop iteration


if __name__ == "__main__":
    main()
