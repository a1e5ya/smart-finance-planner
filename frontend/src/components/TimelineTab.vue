<template>
  <div class="tab-content">
    <div class="container text-center" style="height: 25rem;">
      <div class="flex flex-gap">
        <button class="btn btn-active">Month</button>
        <button class="btn">Quarter</button>
        <button class="btn">Year</button>
      </div>
      <div class="text-medium">Timeline visualization coming soon</div>
      <div class="text-small text-light">Import transactions to see spending trends over time</div>
    </div>

    <div class="grid grid-2">
      <div class="container text-center">
        <div class="text-medium">Financial Goals</div>
        <div class="text-small text-light">
          Set and track financial goals after importing your transaction data.
        </div>
      </div>
      
      <div class="container text-center">
        <div class="text-medium">Scenario Planning</div>
        <div class="text-small text-light">Create what-if scenarios for your financial future.</div>
        <button class="btn">Create Scenario</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TimelineTab'
}
</script>