
# Observer : Dota 2 Time Series Data

The goal of this package is to parse a Dota 2 replay and return time-locked information about all 10 heroes in the game.

## Description

Ever wanted to know exactly where (in coordinates) a player is on the map at a given time ? Find the HP at this time? This is what Observer can do for you.

Given a list of match IDs, Observer parses the file, extracts the information and places in neat pandas Dataframes ready for your analysis. 

All the functions have comments in them so please refer to them for more details on what exactly is happening.

This was completed as an internship project at the [Tilburg University Department of Cognitive Science & A.I](https://www.tilburguniversity.edu/about/schools/tshd/departments/dca/lab).

### Example output 
I have used this package to generate time series data for all of the International 2022 group stage matches. You can find it [here](https://www.kaggle.com/datasets/avngr86/dota-2-ti-2022-group-stage-time-series).

### The Clarity parser

None of this would be possible with the parser built by [Martin Schrodt](https://github.com/spheenik) 

For the Clarity parser, Martin has generated several [examples](https://github.com/skadistats/clarity-examples), including one for position. I have [forked](https://github.com/onedeeper/clarity-examples) this example and modified it to suit my needs. 

Observer uses this code to parse each replay file using some shell commands. The captured output is then modified in the python code which produces the output.

## Getting Started

### Dependencies

Need a java runtime environment 
Built on : 

java version "1.8.0_351"

Java(TM) SE Runtime Environment (build 1.8.0_351-b10)

Java HotSpot(TM) 64-Bit Server VM (build 25.351-b10, mixed mode)

### Installing

Clone this repo
cd into the directory

    pip install . 

### Executing program

From where you're working (notebook, py file): 

    from obs import observer
    matchIds = [6522221361, 6811040499]
    data = observer.GetPosition(matchIds)

Observer first downloads the clarity-examples package from my forked repo to the current working directory. This includes pre-built maven package as well so you don't have to build anything. 

If you want to get different information about a hero, I direct you to [Martin's readme](https://github.com/onedeeper/clarity-examples) on the clarity parser. There, you will be able to learn how to investigate the "send tables" and change the variables (i.e the columns of the dataframes that is finally returned. Ofcourse, this is going to require extensive surgery to Observer which is hard-coded to handle only the variables that I've selected.
```

## Help

I can't even imagine all the ways this thing breaks. I would appreciate any and all feedback. If something breaks, raise an issue and I'll do my best to fix it. 

Please improve this! I'm excited to see this being used and I hope better minds than mine will contribute. 

## Authors

Udesh Habaraduwa

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

Martin Schrodt for taking the time to help me figure out the parser / write an example for me.

[Dr Paris Blom](https://www.tilburguniversity.edu/staff/p-mavromoustakosblom) for discussion and supervision on the project.

> Written with [StackEdit](https://stackedit.io/).
