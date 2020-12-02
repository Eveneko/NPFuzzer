# NPFuzzer

Fuzzing Navigation And Positioning Software

## Steps

### Open Source Project

- PolyU
  - https://github.com/weisongwen/NavCodeMonitor
  - https://github.com/HKUST-Aerial-Robotics/VINS-Fusion
- Github
  - 
- Other
  - https://navigation.ros.org

### Demo

Due some reasons, we should reiplemente the cpp code for demo.

#### Runtime error
- 数据越界
- div 0
- mod 0
- 对栈溢出
- 访问不可读地址
- while - memory/句柄

#### AFL

#### 

## TODO

- [ ] Search 5~6 open source projects
- [ ] Using AFL to test the history version of those projects
- [ ] Find the mutation directions
- [ ] Modify AFL, test Oracle

## Reference

- [AFLplusplus](https://github.com/AFLplusplus/AFLplusplus)
- [RVFuzzer: Finding Input Validation Bugs in Robotic Vehicles through Control-Guided Testing](https://www.usenix.org/system/files/sec19-kim.pdf)
- [fuzzing-survey-TSE2019](./Reference/fuzzing-survey-TSE2019.pdf)
