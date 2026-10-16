# 🌐 IPv6 Subnet Calculator V0.6

[简体中文](README.md) | **English**

## 📖 Overview

IPv6SubnetCalculator is an offline IPv6 subnet calculator for Windows. It calculates network ranges, divides subnets, identifies special-purpose address space, and provides two tabs for calculating and browsing large result sets.

## ✨ Features

- **Subnet calculations:** IPv6 CIDR `/0`–`/128`, network range, subnet counts, and addresses per subnet; lowercase normalization and clear input validation.
- **Prefix and usage analysis:** Common prefix shortcuts, additional subnet bits, special-purpose classifications including ULA, 6to4, multicast and link-local, and deployment guidance with standards references.
- **Two-tab layout:** Use the Calculation tab for inputs, summaries, and address guidance, and the Results tab for the complete table and actions. Switching tabs preserves pagination and locator ranges.
- **Pagination and location:** 25, 50, 100, or 200 rows per page, page navigation, and lookup by IPv6 address, subnet number, address range, or subnet-number range. Range highlighting continues across pages.
- **Selection statistics:** Shows the current-page selection count, first and last indices, continuity, and total address capacity. Non-contiguous selections count only the selected subnets. Hover for exact values or click to copy the statistics.
- **Multiple selection and copying:** Ctrl+click to toggle rows, Shift+click for a contiguous selection, Ctrl+A to select the current page, Ctrl+C to copy in index order, and Esc to clear the selection. Copy the current page or an index range (up to 5,000 rows per range copy), or double-click for details and adjacent-record navigation.
- **Export:** Export all or a selected range to TXT or Excel (XLSX), with size estimates, progress tracking, and cancellation.

## 🆕 What's New in V0.6

- Expanded selection statistics with index span, continuity, address capacity, and copying of exact statistics.
- Separated manual selection from locator highlighting, with distinct counts for the entire range and current-page matches. Paging preserves highlighting without automatically selecting all matching rows.
- Added a Clear Selection icon with a tooltip and a Clear Highlight action. Clearing selection and clearing highlights work independently. Use Ctrl+A to select the current page.
- Improved the Results layout with wrapping statistics and directly visible copy and locator feedback.
- Prefilled range copying with the current locator interval and removed unused legacy icons.

## 📦 Download and Usage

Get the Windows application from GitHub [Releases](../../releases). Enter a network and target prefix, calculate, then switch to the Results tab to browse the full list.

## 💡 Notes

- The default example network is `2026:1015:abcd::/48`.
- IPv6 has no broadcast address; the displayed end address is the last address in the range.
- Manual selection applies to the **current page** and clears when changing pages or page size; switching tabs preserves it. Locating selects only the first match, while range highlighting persists across pages. Entire-range and current-page highlight counts are shown separately.
- Selected address capacity is a mathematical total, not an assignable host count. Very large values use compact display formatting; hover for full values. Copied statistics always contain exact integers.
- Use index-range copying for multiple pages and file export for more than 5,000 records.
- Excel exports support at most 1,048,575 subnet records in one worksheet; use TXT for larger exports.
- Address classification does not imply allocation authorization or public reachability. See the [IANA IPv6 Special-Purpose Address Registry](https://www.iana.org/assignments/iana-ipv6-special-registry).
