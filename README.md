# Gwennen Gambler

This small program will check each item in the Gwennen shop (item gamble) according and show small stats according to poe.ninja.
Should be safe as it does not any send any serverside actions, only copies the item data to clipboard.
It does not filter any uniques (The Saviour is included in table even though it may not be possible to gamble it)

**Demonstration (Please watch before first running it)**: https://www.youtube.com/watch?v=KvKKiI-TdD8

# Important
Should work out of the box for all resolutions with aspect ratios 16:9, 16:10, 24:10. If you have different resolution, or it does not work for you, please follow this quick guide to set it up.([link](https://imgur.com/a/W9MsGh1)). 

# Installation
1. Download latest release
2. Copy the Gwennen Gambler to any folder
3. Run Gambler
4. Wait until console window says "Waiting for (hotkey) press..."
5. Go to Gwennen, open her shop and press (hotkey)
6. Do not move your mouse until it goes to last slot
7. Alt-tab to small con sole window

***
## Config Options
* **Hotkey** - hotkey to start checking (default F6). Should support combinations like "ctrl+r" to start on pressing both CTRL+R
* **RefreshPricesOnStart**: Whether to refresh prices on startup (default True)
* **MouseMoveDelay**: Delay between moving the mouse (default 0.01)
* **Language**: In-game language (not guaranteed to work on others, according to poe.ninja requests). Brasilian = PT, Russian = RU, German = GE, French = FR, Spanish = ES
* **League**: League for price retrieval, supports Standard, Hardcore, Expedition, Hardcore Expedition
* **Unlinked Only**: Whether to ignore separate listings for 5L/6L and only fetch base prices (default True)
* **MinimumMeanChaosValue**: Hides bases with average chaos value below this value (default 0.0)
* **GridTopLeftCornerX**: Top left corner pixel x coordinate (Gwennen shop item grid)
* **GridTopLeftCornerY**: Top left corner pixel y coordinate (Gwennen shop item grid)
* **GridBottomRightCornerX**: Bottom right corner pixel x coordinate (Gwennen shop item grid)
* **GridBottomRightCornerY**: Bottom right corner pixel y coordinate (Gwennen shop item grid)
