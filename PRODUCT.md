# Product

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
React, TypeScript, Vite, Tailwind, shadcn/ui, ECharts and MapLibre; FastAPI and MongoDB;
independent PySpark/Spark SQL batch jobs; Electron for Windows distribution.

## Users
A student demonstrating a Big Data Analytics project and people exploring historical NYC
taxi mobility. The user delegated implementation and visual decisions to the assistant.

## Product Purpose
Explore real taxi demand, geography, trip efficiency and fares, and inspect the processing
and measured performance behind the results. Complete the supplied six-section brief.

## Operating Context
Browser first, desktop second. WSL development and Colab compute. No personal-demo login.
Dashboards must work after Colab disconnects. MongoDB serves precomputed aggregates.

## Capabilities and Constraints
Six sections: overview, demand, geography, trip efficiency, fares and Big Data Lab. Shared
date, borough and zone filters. Known units and dataset versions. Raw data lives outside
MongoDB. Taxi efficiency is not observed road congestion. No fabricated benchmarks or KPIs.

## Evidence on Hand
Q1 2025 TLC source: 11,198,026 raw rows and 11,198,001 pickups within the selected
period, official zone lookup and geometry, verified checksums, completed Spark SQL
analysis, and persistent Drive archives. Source and run evidence are in docs/.

## Brand Commitments
UrbanFlow is the project name. The user supplied functional requirements and delegated style.

## Product Principles
- Make historical evidence and its boundaries visible.
- Keep filters consistent and comparisons mathematically valid.
- Make the underlying big-data processing demonstrable.
- Keep the application independent of temporary batch compute.
