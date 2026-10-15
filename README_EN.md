# 🌐 IPv6 Subnet Calculator

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is a lightweight, offline IPv6 subnet utility for Windows. It helps you inspect network ranges, divide networks into subnets, and save calculation results.

## ✨ V0.1 Features

- Validate IPv6 addresses and CIDR prefixes (`/0`–`/128`), automatically normalizing addresses to their networks
- Calculate network start and end addresses, subnet count, and the number of addresses per subnet
- Display IPv6 addresses in compressed form with a centered subnet list
- Browse subnets in pages of 25, 50, 100, or 200, with navigation and page jumps
- Copy selected subnets or the current page; use `Ctrl+A` to select all visible rows and `Ctrl+C` to copy
- Export all subnets to Excel (XLSX) or TXT, with progress and cancellation
- Warn when the Excel row limit is exceeded and allow a confirmed TXT export instead
- Show clear Chinese-language validation messages

> 💡 **Note:** A single Excel sheet supports at most 1,048,575 subnet records when one row is reserved for headers. TXT export has no equivalent row limit, but very large exports may take substantial time and disk space. IPv6 has no broadcast address; the displayed “last network address” is simply the numerically highest address in the range.

## 📦 Download & Usage

Visit the GitHub [Releases](../../releases) page for available Windows releases. Download `IPv6SubnetCalculator.exe` and run it directly without installation.

Enter the IPv6 network and prefix along with the target prefix, then select “开始计算” (Calculate). Browse pages, copy subnets, or select “导出全部子网” (Export All Subnets) to save a file.

> Refer to the actual files listed on the Releases page. Windows desktop verification is required before final release.
