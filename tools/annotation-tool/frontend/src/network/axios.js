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
