# 双色球历史数据爬虫（ssq-scraper）

一个使用 Python 调用中国福利彩票官网接口的脚本，用来抓取双色球历史开奖数据，并导出为 Excel / CSV。

> 仅用于个人学习与技术研究，请勿用于任何违法用途。

---

## 功能简介

- 调用官网开放接口，一次性获取最近 N 期双色球开奖数据
- 解析字段：
  - 期号（issue）
  - 开奖日期（draw_date）
  - 红球号码（red_numbers）
  - 蓝球号码（blue_numbers）
  - 销售金额（sales）
  - 奖池金额（pool_money）
  - 一/二等中奖情况描述（prize_details）
  - 详情链接（details_link）
- 支持命令行参数：
  - 自定义抓取期数
  - 自定义导出文件名
  - 可选择是否导出 Excel / CSV

---

## 环境准备

1. 安装 Python 3.10+  
   下载地址：<https://www.python.org/downloads/>

2. 安装依赖（在项目目录下）：

```bash
pip install -r requirements.txt
 
##使用方法
在项目目录下执行：

bash
python ssq.py

默认会：

从官网接口抓取最近 2000 期双色球开奖数据

导出到：

ssq_history.xlsx
ssq_history.csv

常用参数
指定抓取期数（例如 500 期）：

bash
复制代码
python ssq.py -n 500
修改导出文件名：

bash
复制代码
python ssq.py -n 1000 --excel my_ssq.xlsx --csv my_ssq.csv
只导出 CSV，不导出 Excel：

bash
复制代码
python ssq.py --excel "" --csv ssq_only.csv

声明
本项目仅供个人学习与技术研究使用，数据来源于中国福利彩票官网。
请遵守相关法律法规，勿将本项目用于任何商业或非法用途。