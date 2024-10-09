"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface BarChartProps {
  data: { label: string; value: number }[];
  // summary: string
}

export default function DownloadableBarChart({ data }: BarChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: height - 100 }); // Adjust height to account for download button and summary
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // Initial setup
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0 || dimensions.height === 0)
      return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 40, right: 30, bottom: 50, left: 60 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    const x = d3.scaleBand().range([0, chartWidth]).padding(0.3);
    const y = d3.scaleLinear().range([chartHeight, 0]);

    x.domain(data.map((d) => d.label));
    y.domain([0, d3.max(data, (d) => d.value) || 0]);

    const chart = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create bars
    chart
      .selectAll(".bar")
      .data(data)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", (d) => x(d.label) || 0)
      .attr("y", (d) => y(d.value))
      .attr("width", x.bandwidth())
      .attr("height", (d) => chartHeight - y(d.value))
      .attr("fill", "#60A5FA")
      .attr("rx", 4)
      .attr("ry", 4);

    // Add X Axis
    chart
      .append("g")
      .attr("transform", `translate(0,${chartHeight})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll("text")
      .attr("class", "axis-text")
      .style("text-anchor", "middle")
      .style("fill", "rgba(255, 255, 255, 0.8)")
      .style("font-size", "12px");

    // Add Y Axis
    chart
      .append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-chartWidth))
      .selectAll("text")
      .attr("class", "axis-text")
      .style("fill", "rgba(255, 255, 255, 0.8)")
      .style("font-size", "12px");

    // Style axis lines
    chart.selectAll(".domain").remove();
    chart.selectAll(".tick line").attr("stroke", "rgba(255, 255, 255, 0.1)");

    // Add title
    svg
      .append("text")
      .attr("class", "chart-title")
      .attr("text-anchor", "middle")
      .attr("x", dimensions.width / 2)
      .attr("y", margin.top / 2)
      .style("fill", "rgba(255, 255, 255, 0.9)")
      .style("font-size", "18px")
      .style("font-weight", "bold")
      .text("Interactive Bar Chart");
  }, [data, dimensions]);

  const handleDownload = () => {
    if (!svgRef.current) return;

    // Clone the SVG node
    const svgNode = svgRef.current.cloneNode(true) as SVGSVGElement;

    // Create a white background
    const background = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "rect"
    );
    background.setAttribute("width", "100%");
    background.setAttribute("height", "100%");
    background.setAttribute("fill", "white");

    // Insert the background as the first child of the SVG
    svgNode.insertBefore(background, svgNode.firstChild);

    // Convert text fill to black for better visibility on white background
    svgNode.querySelectorAll("text").forEach((textElement) => {
      textElement.style.fill = "black";
    });

    // Ensure axis lines are visible
    svgNode.querySelectorAll(".tick line").forEach((line) => {
      line.setAttribute("stroke", "rgba(0, 0, 0, 0.1)");
    });

    // Convert SVG to a string
    const svgData = new XMLSerializer().serializeToString(svgNode);

    // Create a Blob with the SVG data
    const svgBlob = new Blob([svgData], {
      type: "image/svg+xml;charset=utf-8",
    });
    const svgUrl = URL.createObjectURL(svgBlob);

    // Create and trigger download
    const downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = "bar_chart.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    // Clean up the object URL
    URL.revokeObjectURL(svgUrl);
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <div
        ref={containerRef}
        className="w-full relative"
        style={{ height: "400px" }}
      >
        {dimensions.width === 0 || dimensions.height === 0 ? (
          <div className="text-white">Loading chart...</div>
        ) : (
          <svg
            ref={svgRef}
            width={dimensions.width}
            height={dimensions.height}
            className="w-full h-full"
          />
        )}
      </div>
      <Button onClick={handleDownload} className="flex items-center space-x-2">
        <Download className="w-4 h-4" />
        <span>Download Chart</span>
      </Button>
    </div>
  );
}
