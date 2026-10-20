# User Guide

## 1. Calculate a network

Enter an IPv6 CIDR such as **2026:1015:abcd::/48**, then a target prefix such as **64** without a slash. Source and target prefixes range from 0 to 128; the target must be at least the source prefix. Click Calculate or press Enter in either input. Uppercase hexadecimal is normalized to lowercase; host bits are normalized to the containing network.

The summary contains the network range, subnet count, addresses per subnet and additional subnet bits. IPv6 has no broadcast address; the last address is the maximum address in the range. Address capacity is a mathematical count, not an assignable-host guarantee. Review address-use guidance before deployment.

## 2. Browse, select and locate

Results load one page at a time, with 25, 50, 100 or 200 records. Page indices and address counts retain integer precision even for the full IPv6 space. Use the navigation icons or enter a page number.

Choose a location mode: IPv6 address, subnet index, address range or index range. Ranges include both endpoints. Location selects the first matching row and preserves range highlighting across pages. Clear highlighting and Clear selection are separate actions. Ctrl+click and Shift+click select records; Ctrl+A selects the current page, Ctrl+C copies and Esc clears manual selection. Double-click or press Enter for subnet details.

## 3. Copy and export

Copy selected subnets, the entire page, a bounded index range, exact statistics or the calculation summary using the relevant icons. Tooltips explain each action. Range copying is limited to 5,000 records per operation; export larger sets.

Export all subnets or an index range to TXT or Excel (XLSX). A worksheet supports 1,048,575 data rows plus its header; use TXT above this limit. Review size estimates and available space before very large exports. Cancelling removes incomplete temporary files and preserves an existing destination. Excel headers and the worksheet name use the interface language at export start. English output uses “No.”, “IPv6 Subnet” and the worksheet name “IPv6 Subnets”; Chinese output retains its original Chinese labels. Switching languages during export does not change that file. TXT contains one CIDR per line. Addresses, selected ranges and exact index values are unchanged.

## 4. Calculation plans and drag-and-drop

Save the last successful calculation, name, notes, page size, current page, range, page selection and active calculation/tool tab as JSON. Use Ctrl+S, Ctrl+Shift+S for Save As or Ctrl+O to open. Recalculate edited parameters before saving.

Drop one local .json plan anywhere in the main window, including inputs and tables. Validation precedes any replacement. Save, Discard or Cancel protects unsaved work; otherwise confirm replacement. The file is checked again after confirmation. Invalid files and cancellation preserve current work. Source files are not modified by importing, and no extra calculation or export action is triggered beyond restoring the saved calculation/view.

Multiple files, folders, remote links and unsupported formats are rejected. TXT/CIDR lists use Subnet List's Import icon. Finish or cancel background work before dropping a plan. Windows may block Explorer drops into an elevated application; use Open Plan in that case.

## 5. Address tools

Convert one IPv6 address without a prefix or zone identifier into canonical lowercase compression, full expansion and binary. Binary is displayed in 16-bit groups and copied as 128 consecutive bits. IPv4-mapped IPv6 notation is supported.

Two-network analysis identifies equality, containment in either direction, adjacency or separation, with exact overlapping and gap address counts. Adjacency alone does not imply the two CIDRs can merge into one. These tools do not change the calculator's parameters or result.

## 6. Subnet lists

Paste or import a UTF-8 TXT/CIDR file (BOM allowed), one CIDR per line. Blank lines and whole-line # comments are ignored; inline comments, CSV and spreadsheets are unsupported. Limits apply independently: **5,000 validation entries**, **1,048,576 UTF-8 bytes (1 MiB)** and **20,000 physical lines**, including blank/comment lines. Byte size is not a line count.

Validation retains source line numbers and original input. Invalid entries are excluded from relationship checks. Duplicate, containment and adjacent pairs are counted exactly; at most 1,000 detail pairs are retained. Copy normalized valid unique networks or the report. This deduplication does not remove contained networks or merge adjacent ranges. Background tasks can be cancelled without editing input or source files.

## 7. Free space and aggregation

Free Space subtracts the union of occupied entries from the parent network. Every occupied entry must be valid and fully inside the parent; otherwise the entire operation is rejected. An empty list means the full parent is free. Counts are exact integers; overlapping or duplicate occupied entries are counted once.

Free CIDR details are capped at 5,000 while the exact CIDR total and every free interval remain available in the report. Copying a complete CIDR list is disabled if details are truncated. Exact address capacities are available in tooltips and reports.

Aggregation removes duplicate and covered networks and merges only precisely representable adjacent ranges. It preserves exact address coverage without rewriting input, but does not retain allocation hierarchy or business boundaries. Review those boundaries before deployment. Editing inputs invalidates old planning results; editing the parent clears only Free Space. Lists and planning results are not stored in calculation plans; copy input/reports to retain them.

## 8. Language, themes and help

The upper-right icons are **Language → Theme → About**. The globe menu offers 简体中文 and English. Switching is immediate and preserves inputs, results, pages, selections, location highlighting and list/planning state. The language preference is saved for the next launch. User names, notes, paths, input text and original third-party licenses are not translated.

The moon/sun icon or Ctrl+Shift+T switches Light/Dark and remembers the theme. F1 opens the reusable non-modal About window with information, this guide, third-party licenses and legal information. Esc closes dialogs. No Internet connection is required for calculation, switching languages or reading bundled documents.

## 9. Input feedback

Invalid input receives a red border, warning indicator and specific explanation; bottom errors are bold. Editing clears the corresponding field marker and the next action validates again. List errors retain physical line numbers. Copy/export range errors appear inside their dialogs. A plan-file error marks the file status rather than valid current parameters.


## 9. English samples

The source examples include `SubnetList_EN.txt`, `PlanningNetworks_EN.txt` and `OfficeNetwork_EN.json`. Their CIDRs, calculation parameters and view state match the Chinese samples; comments, names and notes use English. Choose a file according to your reading preference. Switching interface languages preserves imported text.


## 10. Address range to CIDR

In Address Tools, enter inclusive first and last IPv6 addresses, then use the conversion icon or press Enter. Supports one address through the complete IPv6 space. The last address must be at least the first; omit CIDR prefixes and zone identifiers. Results cover exactly the range using minimal CIDRs and show an exact address count. Editing either address invalidates old results.

Icons copy the CIDR list or full report, or send the results to Subnet List for automatic checking. Different existing input requires confirmation with No as the default. Busy list tasks block transfer. Calculator results and calculation plans are preserved.
