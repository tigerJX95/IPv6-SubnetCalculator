# 🌐 IPv6 Subnet Calculator V0.4

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is a lightweight, offline IPv6 subnet calculator for Windows. It helps analyze network ranges, divide subnets, recognize special-purpose IPv6 addressing, locate subnets, and export results.

## ✨ Features

- **Network calculation:** Supports IPv6 CIDR `/0`–`/128`; calculates first and last addresses, subnet counts, and address capacity. Normalizes letter case and provides descriptive input errors.
- **Prefix analysis:** Offers commonly used target prefixes, shows additional subnet bits, and explains `/127` and `/128` boundaries.
- **Address type and deployment guidance:** Identifies ULA, link-local, multicast, 6to4, Teredo, documentation addresses, and other known ranges. Displays typical uses, restrictions, and references to IANA and RFCs. Mathematical subnet calculations remain available for special-purpose addresses.
- **Pagination and copy:** Displays 25, 50, 100, or 200 entries per page; supports navigation, jumping, copying selected rows or the current page, and compact statistics for very large results.
- **Unified lookup:** Choose an IPv6 address, subnet index, IPv6 address range, or subnet index range from one dropdown. Matching subnets on the current page are highlighted, including when navigating across pages.
- **Subnet details:** Double-click a subnet to view its address range and address count, with an option to copy the details.
- **Export:** Exports all subnets or an index range to TXT or Excel (XLSX), with progress, cancellation, estimated file size, and large-export warnings.

- **Copy an index range:** Use a dedicated bracket-and-copy icon to copy up to 5,000 subnets by start and end indices; use file export for larger ranges.
- **Browse adjacent subnet details:** Move to the previous or next subnet directly from the detail dialog, with the corresponding row selected.

## 🆕 What's New in V0.4

- Added subnet details with copying and previous/next browsing.
- Combined lookup into one dropdown for individual addresses, subnet indices, and address or index ranges, including highlighting across pages.
- Added range copying (up to 5,000 entries), with a matching blue line icon.

## 📦 Download and Use

Get the Windows application from GitHub [Releases](../../releases) and launch it directly.

Enter an IPv6 network and target prefix, then click the calculate icon. Browse the results, double-click a row for details, or select a lookup mode to locate one subnet or an inclusive range. Use the export icon to save all results or a selected range.

## 💡 Notes

- Default sample network: `2026:1015:abcd::/48`.
- IPv6 has no broadcast address. “Last network address” refers to the numerically highest address in the network.
- An Excel worksheet can contain up to 1,048,575 subnet records plus one header row. Use TXT for larger outputs. Very large exports require sufficient storage and time.
- Address-type guidance does not imply public routability or address assignment rights. See the [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry).
