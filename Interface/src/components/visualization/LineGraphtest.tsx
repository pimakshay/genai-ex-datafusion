"use client";

import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DataPoint {
  x: number;
  y: number;
}

interface LineGraphProps {
  data: {
    xValues: string[];
    yValues: { data: number[]; label: string }[];
  };
  width?: string;
}

export default function LineGraph({ data, width = "100%" }: LineGraphProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: Math.min(400, width * 0.6) });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // Initial setup
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    const chart = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const chartData: DataPoint[] = data.xValues.map((x, i) => ({
      x: parseFloat(x),
      y: data.yValues[0].data[i],
    }));

    const x = d3
      .scaleLinear()
      .domain(d3.extent(chartData, (d) => d.x) as [number, number])
      .range([0, width]);

    const y = d3.scaleLinear().domain([0, 1]).range([height, 0]);

    const line = d3
      .line<DataPoint>()
      .x((d) => x(d.x))
      .y((d) => y(d.y));

    chart
      .append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .attr("color", "#8899A6")
      .selectAll("text")
      .attr("fill", "#8899A6");

    chart
      .append("g")
      .call(d3.axisLeft(y))
      .attr("color", "#8899A6")
      .selectAll("text")
      .attr("fill", "#8899A6");

    chart
      .append("path")
      .datum(chartData)
      .attr("fill", "none")
      .attr("stroke", "#1DA1F2")
      .attr("stroke-width", 1.5)
      .attr("d", line);

    chart
      .selectAll(".dot")
      .data(chartData)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", (d) => x(d.x))
      .attr("cy", (d) => y(d.y))
      .attr("r", 3.5)
      .attr("fill", "#1DA1F2");

    chart
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left)
      .attr("x", 0 - height / 2)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("fill", "#8899A6")
      .text("Survival Rate");

    chart
      .append("text")
      .attr("transform", `translate(${width / 2}, ${height + margin.top + 20})`)
      .style("text-anchor", "middle")
      .style("fill", "#8899A6")
      .text("Time");
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

    // Convert text and lines to black for better visibility on white background
    svgNode.querySelectorAll("text, line, path").forEach((element) => {
      element.setAttribute("fill", "black");
      element.setAttribute("stroke", "black");
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
    downloadLink.download = "line_graph.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    // Clean up the object URL
    URL.revokeObjectURL(svgUrl);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto bg-gray-900 text-gray-200">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">
          Survival Rate Over Time
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center space-y-4">
        <div ref={containerRef} className="w-full" style={{ width }}>
          <svg ref={svgRef} className="w-full h-auto"></svg>
        </div>
        <Button
          onClick={handleDownload}
          className="flex items-center space-x-2"
        >
          <Download className="w-4 h-4" />
          <span>Download Graph</span>
        </Button>
      </CardContent>
    </Card>
  );
}
