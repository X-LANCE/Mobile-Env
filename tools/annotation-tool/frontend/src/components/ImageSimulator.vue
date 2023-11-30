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

Revised by Danyang Zhang @X-Lance based on a private repository at

    https://git.sjtu.edu.cn/549278303/ipa-web
 -->

<template>
  <div>
    <el-row>
      <el-col :span="12">
        <el-card class="box-card">
            <div>
                <b>任务：</b>
                <br>
                <p v-for="(cmd, i) in command" :key="i">
                    {{ cmd }}
                </p>
            </div>
        </el-card>
        <el-card class="box-card">
            <div><b>状态提示：</b>{{ notice }}</div>
        </el-card>
        <el-card class="box-card">
            <div>
                <b>指令：</b>
                <br>
                <ul>
                    <li v-for="(instruct, i) in historyInstructions" :key="i">
                        {{ instruct }}
                    </li>
                    <li v-for="(instruct, i) in newInstructions" :key="i">
                        <b>{{ instruct }}</b>
                    </li>
                </ul>
            </div>
        </el-card>
        <div v-loading="loading" :style="{width: width + 'px', height: height + 'px'}">
          <img
            :src="image"
            ref="image"
            id="screen"
            :width="width + 'px'"
            :height="height + 'px'"
            draggable="false"
            @mousedown="touchstart"
            @mousemove="touch"
            @mouseup="touchend"
          />
        </div>
      </el-col>
      <el-col :span=12>
        <el-card>
            <div>
                <b>回报：</b>{{ accumulatedReward }}
                <span v-show="incrementalReward>0."
                    style="{ font-weight: bold
                           , color: green
                           }"
                    >
                    + {{ incrementalReward }}
                </span>
                <br>
                <b>过程是否完成：</b>
                <span :style="episodeEndLattern">{{ episodeEndString }}</span>
            </div>
        </el-card>
        <el-card>
            <div v-for="(word, index) in vocabulary" :key="index">
                <el-button :disabled="loading" @click="inputToken(index)">{{ word }}</el-button>
            </div>
        </el-card>
		<el-card>
			<el-input type="textarea"
				:autosize="{minRows: 5, maxRows: 20}"
				placeholder="请输入给用户的响应"
				v-model="response"
				:disabled="loading"
				>
			</el-input>
			<br>
			<el-button :disabled="loading" @click="sendResponse(response)">发送</el-button>
		</el-card>
        <el-card>
            <div>
                <el-select v-model="taskId"
                    @change="switchTask"
                    :disabled="loading"
                    >
                    <el-option
                        v-for="(taskName, index) in taskList"
                        :key="index"
                        :value="index"
                        :label="taskName"
                        >
                    </el-option>
                </el-select>
            </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
    name: "ImageSimulator",
    data() {
      return { screenWidth: 1080
             , screenHeight: 1920
             , scale: 0.5

             , taskId: 0
             , command: []
             , vocabulary: []

             , image: null
             , loading: false
             , notice: ""
             , response: ""

             , lastTouchTime: Date.now()
             , lastActionTime: Date.now()
             , touched: false
             , timeSlot: 1000./15.

             , accumulatedReward: 0.
             , incrementalReward: 0.
             , episodeEnd: false
             , historyInstructions: []
             , newInstructions: []
             , noticingTime: 2000

             , rewardFuture: null
             , episodeEndFuture: null
             , instructionFuture: null
             };
    },

    props: [ "taskList"
           ],
    emits: [ "switchTask"
           , "touch"
           , "lift"
           , "inputToken"
           , "response"
           , "repeat"
           ],

    computed: {
        width: function () {
          return this.screenWidth * this.scale;
        },
        height: function () {
          return this.screenHeight * this.scale;
        },

        episodeEndLattern() {
            return this.episodeEnd ?
                { fontWeight: "bold"
                , color: "green"
                } :
                { fontWeight: "normal"
                , color: "red"
                };
        },
        episodeEndString() {
            return this.episodeEnd ? "是" : "否";
        }
    },

    mounted: function () {
      this.$emit("switchTask", 0)
      this.loading = true;
      setInterval(() => {this.autoAction();}, 3.*this.timeSlot);
    },

    methods: {
        switchTask(taskId) {
            this.$emit("switchTask", taskId);
        },

        //setTaskList(taskList) {
            //this.taskList = taskList;
        //}
        setCommand(command) {
            this.command = command;
        },
        setVocabulary(vocabulary) {
            this.vocabulary = vocabulary;
        },

        setNotice(notice) {
          this.notice = notice;
        },
        setLoading(loading) {
          this.loading = loading;
        },
        setScreen(image) {
          this.image = image;
          this.loading = false;
        },
        newReward(reward) {
            if(this.rewardFuture!=null)
            {
                clearTimeout(this.rewardFuture);
                this.mergeReward();
            }
            this.incrementalReward = reward;
            this.rewardFuture = setTimeout(() => {this.mergeReward();},
                    this.noticingTime);
        },
        setEpisodeEnd() {
            if(this.episodeEndFuture!=null)
                clearTimeout(this.episodeEndFuture);
            this.episodeEnd = true;
            this.episodeEndFuture = setTimeout(() => {this.autoClearEpisodeEnd();},
                    this.noticingTime+1000);
        },
        newInstruction(instructions) {
            if(this.instructionFuture!=null)
            {
                clearTimeout(this.instructionFuture);
                this.mergeInstructions();
            }
            this.newInstructions = instructions;
            console.log(instructions.toString())
            this.instructionFuture = setTimeout(() => {this.mergeInstructions();},
                    this.noticingTime);
        },

        mergeReward() {
            this.accumulatedReward += this.incrementalReward;
            this.incrementalReward = 0;
            this.rewardFuture = null;
        },
        autoClearEpisodeEnd() {
            this.episodeEnd = false;
            this.accumulatedReward = 0.;
            this.historyInstructions = [];
            this.episodeEndFuture = null;
        },
        clearEpisodeEnd() {
            if(this.episodeEndFuture!=null)
                clearTimeout(this.episodeEndFuture);
            this.autoClearEpisodeEnd();
        },
        mergeInstructions() {
            this.historyInstructions = this.historyInstructions.concat(this.newInstructions);
            this.newInstructions = [];
            this.instructionFuture = null;
        },

        touchstart(e) {
            this.touched = true;
            this.touch(e);
        },
        touch(e) {
          if(this.touched)
          {
              let touchTime = Date.now();
              if(touchTime - this.lastTouchTime >= this.timeSlot)
              {
                  let x = e.offsetX / this.width;
                  let y = e.offsetY / this.height;
                  this.$emit("touch", x, y);
              }
              this.lastTouchTime = touchTime;
              this.lastActionTime = touchTime;
          }
        },
        touchend(e) {
            this.touched = false;
            let x = e.offsetX / this.width;
            let y = e.offsetY / this.height;
            this.$emit("lift", x, y);
            this.lastActionTime = Date.now();
        },
        inputToken(index) {
            this.$emit("inputToken", index)
            this.lastActionTime = Date.now();
        },
		sendResponse(response) {
			this.$emit("response", response)
			this.lastActionTime = Date.now();
		},
        autoAction() {
            if(!this.loading && !this.touched)
            {
                let actionTime = Date.now();
                if(actionTime - this.lastActionTime >= 3.*this.timeSlot)
                {
                    this.$emit("repeat");
                    this.lastActionTime = actionTime;
                }
            }
        }
    }
};
</script>

<style scoped>
.dialog-input-box {
  width: 360px;
}
</style>
