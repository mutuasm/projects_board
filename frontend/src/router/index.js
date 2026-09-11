import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: { name: 'MyWork' } },
  {
    path: '/my-work',
    name: 'MyWork',
    component: () => import('@/pages/MyWork.vue'),
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('@/pages/Projects.vue'),
  },
  {
    path: '/projects/:project',
    component: () => import('@/pages/Project.vue'),
    props: true,
    children: [
      { path: '', redirect: (to) => ({ name: 'Board', params: to.params }) },
      {
        path: 'board',
        name: 'Board',
        component: () => import('@/pages/project/BoardView.vue'),
        props: true,
      },
      {
        path: 'list',
        name: 'TaskList',
        component: () => import('@/pages/project/ListView.vue'),
        props: true,
      },
      {
        path: 'timeline',
        name: 'Timeline',
        component: () => import('@/pages/project/TimelineView.vue'),
        props: true,
      },
      {
        path: 'overview',
        name: 'Overview',
        component: () => import('@/pages/project/OverviewView.vue'),
        props: true,
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory('/project-board'),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
