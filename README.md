1. Install [LifeSlice](http://wanderingstan.github.io/Lifeslice/) and set it to take a screenshot every 5 minutes.

1. Install [phantomjs](http://phantomjs.org/): `brew install phantomjs`

1. Copy rasterize.js and screenshot_browser.py to a folder (I use `~/src/hindsight` below)

1. Add to crontab something like:

    ```
    * * * * * cd /Users/<user>/src/hindsight/ && (python screenshot_browser.py > today.html) && /usr/local/bin/phantomjs rasterize.js file:///Users/<user>/src/hindsight/today.html todayscreens.png >/dev/null 2>&1
    ```

1. Use GeekTool to drag an "Image" widget onto the desktop. Set it to position (0, 0) and drag its width/height to fill the size of the screen. Set its location to todayscreens.png generated above. Set to refresh every 45(?) seconds.

    _(I use an image widget instead of a web widget because the image can stretch to fill the desktop.)_

1. Optional for privacy: LifeSlice saves both a large and thumbnail-sized screenshot every 5 minutes. Set the larger size to the lowest option (640x400) and add to crontab something to delete those larger files at the top of every hour:

    ```
    0 * * * * rm /Users/<user>/Library/Application\ Support/LifeSlice/screenshot/*
    ```

1. Someday: get this working consistently for a second screen :(
