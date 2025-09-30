import re
from typing import List
from swift.plugin import ORM, orms
from tools.depot import Depot
from swift.utils import get_logger
import time
from tools.rewards import Reward

logger = get_logger()
epoch = 0
project_name = "cjson"

class CountdownORM(ORM):
    def __call__(self, completions,**kwargs) -> List[float]:
        print("llm has generated harnesses. now implement reward computation")
        start_time = time.time()
        rewards = []
        global epoch
        epoch += 1
        for i in range(len(completions)):
            text = completions[i]
            pattern_cpp = r'```cpp\s*(.*?)\s*```'
            pattern_c = r'```c\s*(.*?)\s*```'

            matches_cpp = re.findall(pattern_cpp, text, re.DOTALL)
            matches_c = re.findall(pattern_c, text, re.DOTALL)
            if matches_cpp:
                text = matches_cpp[0].strip()
            elif matches_c:
                text = matches_c[0].strip()
            else:
                text = text.strip()
            
            text = re.sub(r'<cjson/cJSON\.h>', '<cJSON.h>', text)
            output_dir = f"/workspace/output/projects/cjson/harnesses/harness_{str(epoch).zfill(5)}/id_{str(i).zfill(5)}.cpp"
            Depot.create_path(output_dir)  
            with open(output_dir, "w") as f:
                f.write(f"{text}")

            error = None
            # Check for syntax errors
            error = Reward.syntax_error(project_name=project_name,  epoch=epoch,  completion=i, code=text)
            if error:
                if error[1] is None or error[1][0]=="0":
                    rewards.append(0)
                    Reward.save_log(project_name, epoch, i, 0, error, [], kwargs)
                else:
                    rewards.append(-1.0)
                    Reward.save_log(project_name, epoch, i, -1, error, [], kwargs)
                continue

            is_harness = Reward.utility_check(project_name=project_name, epoch=epoch, completion=i)
            if not is_harness[0]:
                rewards.append(-0.5)
                Reward.save_log(project_name, epoch, i, -1, f"less than 3 APIs: {is_harness[1]}", [], kwargs)
                continue
            
            # Check for compilation errors
            error = Reward.compilation_error(project_name=project_name, epoch=epoch, completion=i, additional_flags=["-O2"], debug=True)
            if error:
                rewards.append(0.008)
                Reward.save_log(project_name, epoch, i, 0.008, error,[], kwargs)
                continue
            
            # Check for fuzzing errors
            error = Reward.fuzz_error(project_name=project_name, epoch=epoch, completion=i)
            if error:
                rewards.append(0.04)
                Reward.save_log(project_name, epoch, i, 0.04, error, [], kwargs)
                continue

            # If no errors
            API_Called = Reward.API_coverage(project_name=project_name, epoch=epoch, completion=i)
            loop_score = Reward.count_loops(project_name=project_name, epoch=epoch, completion=i, code = text)
            rewards.append(0.04+API_Called[0]+loop_score)  
            Reward.save_log(project_name, epoch, i, rewards[-1], error, API_Called, kwargs)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Reward computation took {:.2f} seconds".format(elapsed_time))
        return rewards
    
orms['external_countdown'] = CountdownORM