import Vue from 'vue'
import Router from 'vue-router'
//import Base from './views/Base.vue'
import SessionPage from './views/SessionPage'
//import NewDialogPage from './views/NewDialogPage'
//import ReviewPage from './views/ReviewPage'

Vue.use(Router)

export default new Router({
    routes: [
        { path: '/'
        , name: 'SessionPage'
        , component: SessionPage
        }
    ]
})
