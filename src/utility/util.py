from mylib import msutils
        

def writeToFile(base_dir, pack, filename, content):
    dir = base_dir / pack.replace(".", "/")
    msutils.mkdirP(str(dir))
    path = dir / filename

    with open(str(path), mode="w+") as f:
        f.write(content)
