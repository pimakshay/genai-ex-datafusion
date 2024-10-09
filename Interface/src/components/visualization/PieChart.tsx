"use client";

import React, { useRef, useEffect, useState, useMemo } from "react";
import * as d3 from "d3";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface PieChartProps {
  data: { label: string; value: number }[];
}

export default function ResponsivePieChart({ data }: PieChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [isInitialRender, setIsInitialRender] = useState(true);

  const colorScheme = useMemo(
    () => [
      "#1E40AF",
      "#047857",
      "#B91C1C",
      "#6D28D9",
      "#92400E",
      "#065F46",
      "#831843",
      "#3730A3",
      "#7C2D12",
      "#1F2937",
    ],
    []
  );

  const pie = useMemo(
    () =>
      d3
        .pie<{ label: string; value: number }>()
        .sort(null)
        .value((d) => d.value),
    []
  );

  const color = useMemo(() => d3.scaleOrdinal(colorScheme), [colorScheme]);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: Math.min(width, height) });
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

    const { width, height } = dimensions;
    const radius = Math.min(width, height) / 2;
    const innerRadius = radius * 0.6;

    const arc = d3
      .arc<d3.PieArcDatum<{ label: string; value: number }>>()
      .innerRadius(innerRadius)
      .outerRadius(radius)
      .cornerRadius(8);

    const hoverArc = d3
      .arc<d3.PieArcDatum<{ label: string; value: number }>>()
      .innerRadius(innerRadius)
      .outerRadius(radius + 10)
      .cornerRadius(8);

    const labelArc = d3
      .arc<d3.PieArcDatum<{ label: string; value: number }>>()
      .innerRadius(radius * 0.9)
      .outerRadius(radius * 0.9);

    const g = svg
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    const arcs = g
      .selectAll(".arc")
      .data(pie(data))
      .enter()
      .append("g")
      .attr("class", "arc");

    arcs
      .append("path")
      .attr("d", arc)
      .attr("fill", (d) => color(d.data.label) as string)
      .attr("stroke", "#000")
      .attr("stroke-width", 2);

    if (isInitialRender) {
      arcs
        .select("path")
        .transition()
        .duration(1000)
        .attrTween("d", function (d) {
          const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
          return function (t) {
            return arc(interpolate(t)) || "";
          };
        })
        .on("end", () => setIsInitialRender(false));
    }

    const text = arcs
      .append("text")
      .attr("transform", (d) => `translate(${labelArc.centroid(d)})`)
      .attr("dy", ".35em")
      .attr("text-anchor", "middle");

    text
      .append("tspan")
      .attr("x", 0)
      .attr("y", "-0.7em")
      .style("font-weight", "bold")
      .style("font-size", "12px")
      .style("fill", "#ffffff")
      .text((d) => d.data.label);

    text
      .filter((d) => d.endAngle - d.startAngle > 0.25)
      .append("tspan")
      .attr("x", 0)
      .attr("y", "1em")
      .style("fill", "#ffffff")
      .style("font-size", "10px")
      .text((d) => d.data.value.toString());

    // Interactivity
    arcs
      .on("mouseover", function (event, d) {
        d3.select(this)
          .select("path")
          .transition()
          .duration(200)
          .attr("d", hoverArc);

        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip
          .html(`${d.data.label}: ${d.data.value}`)
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY - 28 + "px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .select("path")
          .transition()
          .duration(200)
          .attr("d", arc);

        tooltip.transition().duration(500).style("opacity", 0);
      });

    // Center text
    const centerText = g
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("class", "center-text")
      .style("font-size", "16px")
      .style("fill", "#ffffff");

    centerText.append("tspan").attr("x", 0).attr("y", "-0.7em").text("Total");

    centerText
      .append("tspan")
      .attr("x", 0)
      .attr("y", "1em")
      .text(d3.sum(data, (d) => d.value).toString());

    // Tooltip
    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background-color", "rgba(0, 0, 0, 0.8)")
      .style("color", "#ffffff")
      .style("padding", "8px")
      .style("border-radius", "4px")
      .style("font-size", "12px")
      .style("pointer-events", "none");

    return () => {
      tooltip.remove();
    };
  }, [data, dimensions, pie, color, isInitialRender]);

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
    downloadLink.download = "pie_chart.svg";
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
            aria-label="Interactive pie chart showing data distribution"
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
