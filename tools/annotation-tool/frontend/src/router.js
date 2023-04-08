// Copyright 2023 SJTU X-Lance Lab
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// 
// Revised by Danyang Zhang @X-Lance based on a private repository at
// 
//     https://git.sjtu.edu.cn/549278303/ipa-web

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
