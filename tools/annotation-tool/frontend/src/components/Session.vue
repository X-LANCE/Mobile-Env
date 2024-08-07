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
  <ImageSimulator
    @switchTask="switchTask"
    @touch="touch"
    @lift="lift"
    @inputToken="inputToken"
	@response="sendResponse"
    @repeat="repeat"
    @adbc="sendAdb"
    :task-list="taskList"
    ref="simulator"
  ></ImageSimulator>
</template>

<script>
import ImageSimulator from "./ImageSimulator.vue";
import { net_reset
       , netSwitchTask
       , net_do_action
       } from "@/network";

// function sleep(time) {
//   return new Promise((resolve) => setTimeout(resolve, time));
// }

export default {
  name: "Session",
  data() {
    return { taskList: []
           , taskId: 0

           , actionTouch: 0
           , actionLift: 1
           , actionRepeat: 2
           , actionText: 3
           , actionADB: 4
           };
  },

  async beforeMount() {
    let response = await net_reset({});
    this.taskList = response.taskList;
  },

  methods: {
    async switchTask(index) {
        this.noticeProcessing();
        this.taskId = index;
        let response = await netSwitchTask({"task": index});
        this.$refs.simulator.setCommand(response.command);
        this.$refs.simulator.setVocabulary(response.vocabulary);
        this.$refs.simulator.setScreen(response.observation);
        this.$refs.simulator.clearEpisodeEnd();
        this.noticeReady();
    },
    touch(x, y) {
        return this.sendAction({ "actionType": this.actionTouch
                               , "touchPosition": [x, y]
                               });
    },
    lift(x, y) {
        this.noticeProcessing();
        return this.sendAction({ "actionType": this.actionLift
                               , "touchPosition": [x, y]
                               });
    },
    inputToken(index) {
        this.noticeProcessing();
        return this.sendAction({ "actionType": this.actionText
                               , "inputToken": index
                               });
    },
	sendResponse(response) {
		this.noticeProcessing();
		return this.sendAction( { "actionType": this.actionLift
								, "touchPosition": [0, 0]
								, "response": response
								}
                              );
	},
    repeat() {
        return this.sendAction({ "actionType": this.actionRepeat
                               , "touchPosition": [0, 0]
                               });
    },
	sendAdb(command) {
		return this.sendAction( { "actionType": this.actionADB
								, "command": command
								}
							  );
	}

    async sendAction(action) {
		let timestamp = Date.now();
		action.timestamp = timestamp;
        let response = await net_do_action(action)
		if(new Date(response.timestamp)>=timestamp)
			this.$refs.simulator.setScreen(response.observation);
        if(response.instruction.length>0)
            this.$refs.simulator.newInstruction(
                response.instruction);
		// TODO: append ADB output
        if(response.episodeEnd)
        {
            this.noticeEpisodeEnd(response.reward, response.succeeds);
            await this.switchTask(this.taskId);
            this.noticeReady();
        }
        else if(response.reward>0)
            this.noticeReward(response.reward);
        else
            this.noticeReady();
    },

    noticeProcessing() {
        this.$refs.simulator.setLoading(true);
        this.$refs.simulator.setNotice("后台运行中，请稍后……");
    },
    noticeReady() {
        this.$refs.simulator.setNotice("已就绪，请操作。");
        this.$refs.simulator.setLoading(false);
    },
    noticeEpisodeEnd(reward, succeeds) {
        this.$refs.simulator.newReward(reward);
        this.$refs.simulator.setEpisodeEnd(succeeds);
		if(succeeds)
			success_notifier = "已成功达成任务目标"
		else if(succeeds===null)
			success_notifier = "系统出错"
		else
			success_notifier = "任务失败"
		this.$refs.simulator.setNotice(`${success_notifier}，共获得${reward}点分数。系统正在重置，请勿操作。`);
        this.$refs.simulator.setLoading(true);
    },
    noticeReward(reward) {
        this.$refs.simulator.newReward(reward);
        this.$refs.simulator.setNotice(`获得了${reward}点分数！`);
        this.$refs.simulator.setLoading(false);
    }
  },
  components: {
    ImageSimulator,
  },
};
</script>

<style scoped>
.dialog-main {
  background-color: white;
  width: 90%;
  height: 650px;
  border-radius: 10px;
  border: 1px gray solid;
  overflow: hidden;
}

.dialog-header {
  border-bottom: 1px gray solid;
  height: 8%;
  padding: 5px 0 0 10px;
}

.dialog-dialog {
  height: 84%;
  overflow-y: auto;
  overflow-x: hidden;
}

.dialog-input {
  height: 8%;
  overflow: hidden;
  display: flex;
  flex-direction: column-reverse;
}

.dialog-tag {
  height: 30px;
  width: 50px;
  margin: 10px 0 10px 10px;
}
.name-input {
  width: 30%;
}

.color-success {
  color: #67c23a;
}
.color-info {
  color: #909399;
}
</style>
