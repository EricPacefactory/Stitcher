# Video Stitcher

Helper script for (losslessly) stitching multiple videos together using ffmpeg.

(Only tested on: Linux Mint 19.1 Tessa, Python 3.5+)

## Requirements

The cli version of this tool relies on a program called [ranger](https://github.com/ranger/ranger). On Ubuntu, this can be installed as follows:

`sudo apt install ranger`

The gui version of this tool relies on [tkinter]([TkInter - Python Wiki](https://wiki.python.org/moin/TkInter)). On Ubuntu, this can be installed as follows:

`sudo apt install python3-tk`

Additionally, this script uses [FFmpeg](https://ffmpeg.org/) to clip videos. On Ubuntu, this can be installed as follows:

`sudo apt install ffmpeg`

## Usage

This script is entirely command-line based. Launch using:

`python3 stitcher_cli.py`

The user is first prompted with a message about using ranger. The file system can be navigated with arrow keys in order to find a video. Use `Spacebar` to select multiple videos for stitching, use the ```Enter``` key to complete selection.

Following the file selection, the list of files for stitching will be printed out, in the order they will be stitched. Additionally, the user will be prompted to enter a file name for the saved (stitched) result. Assuming the name enttry is not cancelled, the videos will be stitched! It should only take a few seconds at most.

**Note1:** The file extension will be chosen based on the input files for stitching. Any extension entered by the user will be ignored.

# Script Arguments

This script accepts multiple input arguments:

```
-f / --folder : <String>
    Folder containing videos to stitch (use this to skip file selection)

-n / --outname : <String>
    Output file name (no extension)
    
-p / --outpath : <String>
    Folder path for the output file (defaults to the same as the source)  
```

## TODOs

- Option to change video encoding? (e.g. convert to h264)
- Option to timelapse
- Option to resize resulting video
