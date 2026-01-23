<script lang="ts">
  import { Line } from 'svelte-chartjs';
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale,
    Filler
  } from 'chart.js';

  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale,
    Filler
  );

  export let data: { date: string; rate: number | null }[] = [];
  export let color = '#3b82f6'; // blue-500 default

  $: chartData = {
    labels: data.map(d => d.date),
    datasets: [
      {
        fill: true,
        data: data.map(d => d.rate),
        borderColor: color,
        backgroundColor: color + '20', // transparent version
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.4
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { 
        enabled: true,
        mode: 'index',
        intersect: false
      }
    },
    scales: {
      x: { display: false },
      y: { display: false }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };
</script>

<div class="h-16 w-32">
  <Line data={chartData} {options} />
</div>
