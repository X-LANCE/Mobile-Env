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
