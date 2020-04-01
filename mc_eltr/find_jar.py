import os
import sys
from pathlib import Path

# find the path of the Minecraft folder
def find_mc_folder():
    # attempt to set the location of minecraft .jar
    # windows/cygwin
    mc_folder = None
    if sys.platform == "win32":
        mc_folder = Path(os.getenv("APPDATA")) / ".minecraft"
    # mac
    elif sys.platform == "darwin":
        mc_folder = Path.home() / "Library" / "Application Support" / "minecraft"
    # linux/other
    return mc_folder


# find the path of the Minecraft .jar
def find_jar():
    jar = None
    # the minecraft folder
    mc_folder = find_mc_folder()
    if mc_folder is not None:
        jars_found = list(str(jar) for jar in (mc_folder / "versions/").glob("*/*.jar"))
        jar = Path(sorted(jars_found, reverse=True)[0])
    return jar