<script lang="ts">
  import Chart from 'chart.js/auto';
  import { onMount, onDestroy } from 'svelte';

  export let data: { date: string; rate: number | null }[] = [];
  export let color = '#3b82f6'; // blue-500 default

  let canvas: HTMLCanvasElement;
  let chart: Chart;

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

  const options: any = {
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

  onMount(() => {
    if (canvas) {
      chart = new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: options
      });
    }
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });

  $: if (chart && chartData) {
    chart.data = chartData;
    chart.update('none');
  }
</script>

<div class="h-16 w-32">
  <canvas bind:this={canvas}></canvas>
</div>
