"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface DataPoint {
  x: number;
  y: number;
  id: number;
}

interface Series {
  data: DataPoint[];
  label: string;
}

interface ScatterPlotProps {
  data: {
    series: Series[];
  };
}

export default function D3ScatterPlot({ data }: ScatterPlotProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: width * 0.5 }); // Set height to 50% of width for a 2:1 aspect ratio
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // Initial setup
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (!svgRef.current || data.series.length === 0 || dimensions.width === 0)
      return;

    const margin = { top: 20, right: 20, bottom: 40, left: 40 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const xScale = d3
      .scaleLinear()
      .domain([0, d3.max(data.series[0].data, (d) => d.x) as number])
      .range([0, width]);

    const yScale = d3.scaleLinear().domain([0, 1]).range([height, 0]);

    // Add X axis
    svg
      .append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(-height).tickPadding(10))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#888").attr("opacity", 0.2)
      )
      .append("text")
      .attr("x", width / 2)
      .attr("y", 35)
      .attr("fill", "#fff")
      .attr("text-anchor", "middle")
      .text("X Axis");

    // Add Y axis
    svg
      .append("g")
      .call(d3.axisLeft(yScale).tickSize(-width).tickPadding(10))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#888").attr("opacity", 0.2)
      )
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -height / 2)
      .attr("fill", "#fff")
      .attr("text-anchor", "middle")
      .text("Y Axis");

    // Add dots
    svg
      .append("g")
      .selectAll("dot")
      .data(data.series[0].data)
      .enter()
      .append("circle")
      .attr("cx", (d) => xScale(d.x))
      .attr("cy", (d) => yScale(d.y))
      .attr("r", 5)
      .style("fill", "#8884d8")
      .style("opacity", 0.7)
      .on("mouseover", function (event, d) {
        d3.select(this).transition().duration(100).attr("r", 8);

        svg
          .append("text")
          .attr("class", "tooltip")
          .attr("x", xScale(d.x) + 10)
          .attr("y", yScale(d.y) - 10)
          .text(`(${d.x.toFixed(2)}, ${d.y.toFixed(2)})`)
          .style("font-size", "12px")
          .style("fill", "#fff");
      })
      .on("mouseout", function () {
        d3.select(this).transition().duration(100).attr("r", 5);

        svg.selectAll(".tooltip").remove();
      });
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
    downloadLink.download = "scatter_plot.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    // Clean up the object URL
    URL.revokeObjectURL(svgUrl);
  };

  return (
    <Card className="w-full max-w-3xl mx-auto bg-gray-800 text-white">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">
          D3 Scatter Plot
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center space-y-4">
        <div ref={containerRef} className="w-full">
          <svg ref={svgRef} className="w-full h-auto"></svg>
        </div>
        <Button
          onClick={handleDownload}
          className="flex items-center space-x-2"
        >
          <Download className="w-4 h-4" />
          <span>Download Plot</span>
        </Button>
      </CardContent>
    </Card>
  );
}
