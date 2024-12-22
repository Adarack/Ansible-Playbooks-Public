The code in the smartctl-helper file might need to be adjusted for your envionment.

This is the original version of the script.

#!/bin/bash

smartctl --scan | awk '{ print $1 }' | while read dev; do
    temp="$(smartctl -a $dev | grep "Temperature:" | awk '{ print $2 }')"
    echo "$dev:$temp"
done

And here is what I needed for my pi's

#!/bin/bash

smartctl --scan | awk '{ print $1 }' | while read dev; do
    temp="$(smartctl -a $dev | grep "Temperature_Celsius" | awk '{ print $10 }')"
    echo "$dev:$temp"
done

As you can see I had to change grep "Temperature:"  to grep "Temperature_Celsius" I also needed to change the { print $2 } to { print $10 }

I cannot get this to work with eMMC storage though.