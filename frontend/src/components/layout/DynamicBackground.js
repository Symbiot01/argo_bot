// File: src/components/layout/DynamicBackground.js
// Description: The component that renders the D3.js geographic background using SVG.


'use client';
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import styles from './DynamicBackground.module.scss';

export default function DynamicBackground() {
  const svgRef = useRef(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const { width, height } = svg.node().getBoundingClientRect();

    // Define projection centered on the Indian Ocean
    const projection = d3.geoMercator()
      .center([70, 5]) // Longitude, Latitude for Indian Ocean
      .scale(width /1.5) // Adjust scale based on width
      .translate([width / 2, height / 2]);

    const pathGenerator = d3.geoPath().projection(projection);

    // Draw Graticule (grid lines)
    const graticule = d3.geoGraticule();
    svg.append('path')
      .datum(graticule)
      .attr('class', styles.grid)
      .attr('d', pathGenerator);

    // Fetch and draw coastline data
    d3.json('/data/coastline.json').then(data => {
      svg.selectAll('.coastline')
        .data(data.features)
        .enter().append('path')
        .attr('class', styles.coastline)
        .attr('d', pathGenerator);
    });

  }, []);

  return (
    <div className={styles.backgroundContainer}>
      <svg ref={svgRef} width="100%" height="100%" />
      {/* Sonar Gradients */}
      <div className={styles.sonarGradient} style={{ width: '800px', height: '800px', top: '10%', left: '20%' }} />
      <div className={styles.sonarGradient} style={{ width: '600px', height: '600px', bottom: '5%', right: '15%', animationDelay: '3s' }} />
    </div>
  );
}