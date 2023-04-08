import axios from '../axios'

export const netSwitchTask = (param) => {
    let result = axios.post("/switchTask", param)
    return result
}

export const net_do_action = (param) => {
	let res = axios.post("/doAction", param)
	return res
}

export const net_reset = (param) => {
	let res = axios.post("/reset", param);
	return res;
}
