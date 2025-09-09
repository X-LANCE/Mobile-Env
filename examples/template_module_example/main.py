#!/usr/bin/python3

from android_env.templates.evaluators import evaluate_llm_agent, evaluate_llm_agent_mp, evaluate_llm_agent_mpi
from pathlib import Path

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, choices=["test_plain", "test_mp", "test_mpi"])
    args: argparse.Namespace = parser.parse_args()

    task_path = Path("taskset")
    avd_name = "Pixel_2_API_30_ga_x64_1"
    save_traj_to = Path("outputs/")
    save_traj_to.mkdir(exist_ok=True)
    tokenizer_path = Path("qwen-2.5-7b-tokenizer")

    model_name = "qwen-2.5-14b"
    api_key = "vllm"
    base_url = "http://127.0.0.1:44509/v1"

    if args.action=="test_plain":
        evaluate_llm_agent( task_path=task_path, avd_name=avd_name, starts_from=0, ends_at=5
                          , save_traj_to=save_traj_to, input_tokenizer=tokenizer_path, max_steps=7
                          , mitm_config={"method": "syscert"}
                          , llm_type="text", prompt_template_path="mobile-env-agent.prompt", prompt_value_macros={"LLM_TYPE": "TEXT"}
                          , model_name=model_name, api_key=api_key, base_url=base_url
                          , env_load_kwargs={ "start_token_mark": "Ġ", "non_start_token_mark": ""
                                            , "run_headless": False
                                            }
                          )
    elif args.action=="test_mp":
        evaluate_llm_agent_mp( task_path=task_path, avd_name=avd_name, starts_from=0, ends_at=5, nb_workers=4
                             , save_traj_to=save_traj_to, input_tokenizer=tokenizer_path, max_steps=7
                             , mitm_config={"method": "syscert"}
                             , llm_type="text", prompt_template_path="mobile-env-agent.prompt", prompt_value_macros={"LLM_TYPE": "TEXT"}
                             , model_name=model_name, api_key=api_key, base_url=base_url
                             , env_load_kwargs={"start_token_mark": "Ġ", "non_start_token_mark": ""}
                             )
    elif args.action=="test_mpi":
        evaluate_llm_agent_mpi( task_path=task_path, avd_name=avd_name, starts_from=0, ends_at=5
                              , save_traj_to=save_traj_to, input_tokenizer=tokenizer_path, max_steps=7
                              , mitm_config={"method": "syscert"}
                              , llm_type="text", prompt_template_path="mobile-env-agent.prompt", prompt_value_macros={"LLM_TYPE": "TEXT"}
                              , model_name=model_name, api_key=api_key, base_url=base_url
                              , env_load_kwargs={"start_token_mark": "Ġ", "non_start_token_mark": ""}
                              )


if __name__ == "__main__":
    main()
