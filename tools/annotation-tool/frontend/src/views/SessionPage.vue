<!-- 
Copyright 2023 SJTU X-Lance Lab

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Created by Danyang Zhang @X-Lance.
 -->

<template>
    <el-container class=".base-container">
        <div class = 'dialogPage-dialog'>
            <Session></Session>
        </div>
    </el-container>
</template>


<script>
import Session from '../components/Session';
export default {
    components:{
        Session
    }
}
</script>

<style scoped>
.dialogPage-dialog {
    height: 80vh;
    width: 100vw;
    padding: 50px;
}
.base-container {
    background-image: url('../assets/bg.png');
    background-repeat: no-repeat;
    background-size: 100% 100%;
    height: 100vh;
    padding: 0;
}
</style>
