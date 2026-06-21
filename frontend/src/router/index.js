import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Projects from '../views/Projects.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Findings from '../views/Findings.vue'
import Dependencies from '../views/Dependencies.vue'
import ImportView from '../views/Import.vue'
import Settings from '../views/Settings.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard },
    { path: '/projects', component: Projects },
    { path: '/projects/:id', component: ProjectDetail },
    { path: '/findings', component: Findings },
    { path: '/dependencies', component: Dependencies },
    { path: '/import', component: ImportView },
    { path: '/settings', component: Settings },
  ],
})
