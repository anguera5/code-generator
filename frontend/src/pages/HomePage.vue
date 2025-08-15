<template>
  <v-container class="py-8">
    <h1 class="text-h4 mb-4">Welcome</h1>
    <p class="text-body-1 mb-6">
      This workspace hosts multiple mini-app modules. Select a project from the menu or cards below.
    </p>
    <v-divider class="mb-6" />
    <h2 class="text-h5 mb-4">Available Modules</h2>
    <v-row>
      <v-col v-for="m in modules" :key="m.path" cols="12" md="6" lg="4">
        <v-card :to="m.path" variant="outlined" class="hover-raise">
          <v-card-title>{{ m.title }}</v-card-title>
          <v-card-text>{{ m.description }}</v-card-text>
          <v-card-actions>
            <v-btn color="primary" variant="text" :to="m.path">Open</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <!--
    <v-alert type="info" variant="tonal" class="mt-8">
      Add a new module by creating a folder under <code>src/modules/&lt;name&gt;</code> and registering it in <code>src/modules/index.ts</code>.
    </v-alert>
    -->
  </v-container>
</template>

<script setup lang="ts">
import { modules } from '../modules'
</script>

<style scoped>
.hover-raise { transition: box-shadow .25s ease; }
.hover-raise:hover { box-shadow: 0 4px 14px rgba(0,0,0,.18); }
</style>
