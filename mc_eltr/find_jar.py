import os
import sys
from pathlib import Path

# find the path of the Minecraft folder
def find_mc_folder(jar_not_found):
    # attempt to set the location of minecraft .jar
    # windows/cygwin
    if sys.platform == "win32":
        mc_folder = Path(os.getenv("APPDATA")) / ".minecraft"
    # mac
    elif sys.platform == "darwin":
        mc_folder = Path.home() / "Library" / "Application Support" / "minecraft"
    # linux/other
    else:
        print(
            "Automatically finding minecraft .jar is only implemented for windows and mac.\n"
            + jar_not_found
        )
        exit()
    if not mc_folder.exists():
        print(
            "Did not find Minecraft folder at the expected location ("
            + str(mc_folder)
            + ")\n"
            + jar_not_found
        )
        exit()
    else:
        return mc_folder


# find the path of the Minecraft .jar
def find_jar(args, prog):
    # message to print if automatically finding the jar fails
    jar_not_found = (
        "Please specify the location of the minecraft .jar using the -j option e.g.\n"
        + prog
        + " -j "
        + str(Path.home() / "/.minecraft/versions/1.5.2/1.5.2.jar")
    )

    jar = None

    if args.jar is not None:
        if not Path(args.jar).is_file:
            print("Could not find the specifified minecraft .jar file " + args.jar)
        else:
            jar = Path(args.jar)
    else:
        # the minecraft folder
        mc_folder = find_mc_folder(jar_not_found)
        jars_found = list(str(jar) for jar in (mc_folder / "versions/").glob("*/*.jar"))
        jar = Path(sorted(jars_found, reverse=True)[0])

    if jar is None:
        print("Unable to find the minecraft .jar\n" + jar_not_found)
        exit()
    else:
        print("Found Minecraft version " + jar.stem)
        return jar