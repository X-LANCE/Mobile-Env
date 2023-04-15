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

import Axios from 'axios';
import { Message } from 'element-ui';
import router from '../router'
//import store from '../store'

const axios = Axios.create();
export const debug  = false;
// export const base_url = 'http://202.120.38.156:55560'
export const base_url = ''

axios.interceptors.response.use(function(response) {
    // Do something with response data
    if (response.data['status'] == -2){
        Message.error("认证失败");
        //store.commit('user/exitUser');
        router.replace('/')
    }
    return response.data;
}, function(error) {
    // Do something with response error
    console.log("连接出错",error);
    Message.error("系统出错");
    return {'status':-3,'error':'网络错误'};
    // return Promise.reject(error);
});

export default axios;
