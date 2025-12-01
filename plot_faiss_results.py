
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def parse_hnsw_results(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
        add_time_us = float(re.search(r"add_wall_time_us t=([\d.]+)", content).group(1))
        search_time_us = float(re.search(r"search_wall_time_us t=([\d.]+)", content).group(1))
    return {'add_time_s': add_time_us / 1_000_000, 'search_time_ms': search_time_us / 1_000}

def parse_perf_results(file_path):
    data = {"dtlb_misses": 0, "page_faults": 0}
    with open(file_path, 'r') as f:
        for line in f:
            if 'page-faults' in line:
                faults_str = re.search(r"([\d,]+)\s+page-faults", line).group(1)
                data['page_faults'] = int(faults_str.replace(',', ''))
            if 'dTLB-load-misses' in line:
                misses_str = re.search(r"([\d,]+)\s+dTLB-load-misses", line).group(1)
                data['dtlb_misses'] = int(misses_str.replace(',', ''))
    return data

def main():
    results_dir = 'test_results_tcmalloc/faiss'
    settings = ['never', 'madvise', 'always']
    nb_values = [100000, 1000000]
    for nb in nb_values:
        print(f"--- Generating plots for NB = {nb:,} ---")
        data = []
        for setting in settings:
            hnsw_file = os.path.join(results_dir, f"hnsw_results_{setting}_nb{nb}.txt")
            perf_file = os.path.join(results_dir, f"perf_results_{setting}_nb{nb}.txt")
            if not (os.path.exists(hnsw_file) and os.path.exists(perf_file)):
                print(f"Warning: Result files for setting '{setting}' with nb={nb} not found. Skipping.")
                continue
            result = {'setting': setting}
            result.update(parse_hnsw_results(hnsw_file))
            result.update(parse_perf_results(perf_file))
            data.append(result)
        if not data:
            print(f"Error: No data was parsed for nb={nb}. Please check the 'test_results' directory.")
            continue

        df = pd.DataFrame(data)
        df.set_index('setting', inplace=True)
        plt.style.use('seaborn-v0_8-whitegrid')
        nb_str = f"{nb // 1000}k" if nb < 1000000 else f"{nb // 1000000}M"

        # Plot 1: Index Creation Time
        fig1, ax1 = plt.subplots()
        df['add_time_s'].plot(kind='bar', ax=ax1, color=['#d9534f', '#5cb85c', '#5bc0de'], rot=0)
        ax1.set_title(f'Index Creation Time (nb={nb_str})', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Wall Time (seconds)')
        ax1.set_xlabel('')
        for container in ax1.containers:
            ax1.bar_label(container, fmt='%.2fs')
        fig1.tight_layout()
        plot1_path = os.path.join(results_dir, f'plot_index_creation_time_nb{nb}.png')
        fig1.savefig(plot1_path)
        print(f"Saved index creation plot to: {plot1_path}")

        # Plot 2: Search Time
        fig2, ax2 = plt.subplots()
        df['search_time_ms'].plot(kind='bar', ax=ax2, color=['#d9534f', '#5cb85c', '#5bc0de'], rot=0)
        ax2.set_title(f'Search Performance (nb={nb_str})', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Wall Time (milliseconds)')
        ax2.set_xlabel('')
        for container in ax2.containers:
            ax2.bar_label(container, fmt='%.2fms')
        fig2.tight_layout()
        plot2_path = os.path.join(results_dir, f'plot_search_performance_nb{nb}.png')
        fig2.savefig(plot2_path)
        print(f"Saved search performance plot to: {plot2_path}")

        # Plot 3: dTLB Load Misses
        fig3, ax3 = plt.subplots()
        df['dtlb_misses'].plot(kind='bar', ax=ax3, color=['#d9534f', '#5cb85c', '#5bc0de'], rot=0)
        ax3.set_title(f'dTLB Load Misses (nb={nb_str})', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Misses (Log Scale)')
        ax3.set_xlabel('')
        ax3.set_yscale('log')  # Use log scale due to huge difference in misses for some
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f'{int(y):,}'))
        for container in ax3.containers:
            ax3.bar_label(container, labels=[f'{v:,.0f}' for v in container.datavalues])
        fig3.tight_layout()
        plot3_path = os.path.join(results_dir, f'plot_dtlb_misses_nb{nb}.png')
        fig3.savefig(plot3_path)
        print(f"Saved dTLB misses plot to: {plot3_path}")
        # Plot 4: dTLB Load Misses
        fig4, ax4 = plt.subplots()
        df['page_faults'].plot(kind='bar', ax=ax4, color=['#d9534f', '#5cb85c', '#5bc0de'], rot=0)
        ax4.set_title(f'Page Faults (nb={nb_str})', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Faults (Log Scale)')
        ax4.set_xlabel('')
        ax4.set_yscale('log')  # Use log scale due to huge difference in misses for some
        ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f'{int(y):,}'))
        for container in ax4.containers:
            ax4.bar_label(container, labels=[f'{v:,.0f}' for v in container.datavalues])
        fig4.tight_layout()
        plot4_path = os.path.join(results_dir, f'plot_page_faults_nb{nb}.png')
        fig4.savefig(plot4_path)
        print(f"Saved page faults plot to: {plot4_path}")
        plt.close('all') # Close all figures before the next loop iteration


if __name__ == '__main__':
    main()
