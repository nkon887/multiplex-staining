import subprocess


def run_shell_process(command, out=False):
    if out:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
        out = result.stdout
        return out
    else:
        subprocess.run(" && ".join(command), shell=True)
        return
