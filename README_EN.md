# 🌐 IPv6 Subnet Calculator

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is a lightweight, offline IPv6 subnet utility for Windows. It helps you inspect network ranges, divide networks into subnets, and save calculation results.

## ✨ Features

- Validate IPv6 addresses and CIDR prefixes (`/0`–`/128`), automatically normalizing addresses to their networks
- Calculate network start and end addresses, subnet count, and the number of addresses per subnet
- Display IPv6 addresses in compressed form with a centered subnet list
- Browse subnets in pages of 25, 50, 100, or 200, with navigation and page jumps
- Copy selected subnets or the current page; use `Ctrl+A` to select all visible rows and `Ctrl+C` to copy
- Export all subnets to Excel (XLSX) or TXT, with progress and cancellation
- Warn when the Excel row limit is exceeded and allow a confirmed TXT export instead
- Show clear Chinese-language validation messages

> 💡 **Note:** A single Excel sheet supports at most 1,048,575 subnet records when one row is reserved for headers. TXT export has no equivalent row limit, but very large exports may take substantial time and disk space. IPv6 has no broadcast address; the displayed “last network address” is simply the numerically highest address in the range.

## 🆕 New in V0.3

- **Prefix division analysis**: The summary shows additional subnet bits (for example, `/48 → /64` adds 16 bits), alongside the existing subnet-count result.
- **Common-prefix quick selection**: Pick `/48`, `/56`, `/60`, `/64`, `/127`, or `/128` where valid for the source network. Inapplicable values are excluded, selection recalculates immediately, and manual prefix entry remains available.

- **IPv6 address classification**: The calculation summary identifies common address categories, their intended use, and relevant standards.
- **Deployment guidance**: Distinguishes global unicast, ULA for private networks/VPNs, link-local, historic transition mechanisms, and documentation-only ranges; mixed ranges receive a caution.
- **No artificial calculation restrictions**: Subnet arithmetic remains available for special-purpose ranges, without implying Internet reachability or allocation rights.

> 💡 **Address usage:** Classification uses commonly registered IANA special-purpose prefixes and relevant RFCs; it does not guarantee current registry status, allocation rights, or Internet reachability. Reference: https://www.iana.org/assignments/iana-ipv6-special-registry

## 📦 Download & Usage

Visit the GitHub [Releases](../../releases) page for available Windows releases. Download `IPv6SubnetCalculator.exe` and run it directly without installation.

Enter the IPv6 network and prefix along with the target prefix, then select “开始计算” (Calculate). Browse pages, copy subnets, locate the subnet containing an address, or export all or a selected range to a file.

