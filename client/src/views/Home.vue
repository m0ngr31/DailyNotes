<template>
  <div class="columns no-overflow no-margin">
    <div class="column sidebar">
      <div class="columns light-white center-columns">
        <div class="column">
          <b-icon
            icon="book-open"
            size="is-large"
            style="margin-top: .8em"
          >
          </b-icon>
        </div>
        <div class="column is-four-fifths">
          <span class="fa-3x">DailyNotes</span>
        </div>
      </div>
      <Calendar />
      <Tags />
    </div>
    <div class="column is-four-fifths no-padding">
      <router-view :key="$route.path"></router-view>
    </div>
  </div>
</template>

<script>
import Calendar from "@/components/Calendar.vue";
import Tags from "@/components/Tags.vue";

export default {
  name: "home",
  components: {
    Calendar,
    Tags
  },
  metaInfo: {
    title: 'Home',
  }
};
</script>

<style scoped>
.no-overflow {
  overflow: hidden;
}

.no-margin {
  margin: 0px;
}

.no-padding {
  padding: 0px;
}

.center-columns {
  margin-left: auto;
  margin-right: auto;
}

.sidebar {
  overflow-y: auto;
  height: 100vh;
  overflow-x: hidden;
}
</style>