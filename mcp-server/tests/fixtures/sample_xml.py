"""
Sample XML content for testing.
"""

# Valid Draw.io XML samples
VALID_DRAWIO_XML = '''<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI" version="22.1.0">
  <diagram name="Page-1" id="page-id">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Start" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="80" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="3" value="Process" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="200" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="4" value="End" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="300" width="80" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="5" value="" style="endArrow=classic;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="2" target="3">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="200" y="250" as="sourcePoint"/>
            <mxPoint x="250" y="200" as="targetPoint"/>
          </mxGeometry>
        </mxCell>
        <mxCell id="6" value="" style="endArrow=classic;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="3" target="4">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="200" y="350" as="sourcePoint"/>
            <mxPoint x="250" y="300" as="targetPoint"/>
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

MINIMAL_VALID_XML = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

AWS_DIAGRAM_XML = '''<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI" version="22.1.0">
  <diagram name="AWS Architecture" id="aws-arch">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="aws-cloud" value="AWS Cloud" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;" vertex="1" parent="1">
          <mxGeometry x="50" y="50" width="700" height="500" as="geometry"/>
        </mxCell>
        <mxCell id="vpc" value="VPC (10.0.0.0/16)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#248814;dashed=0;" vertex="1" parent="aws-cloud">
          <mxGeometry x="30" y="40" width="640" height="420" as="geometry"/>
        </mxCell>
        <mxCell id="ec2" value="EC2 Instance&#xa;Web Server" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="vpc">
          <mxGeometry x="100" y="100" width="48" height="48" as="geometry"/>
        </mxCell>
        <mxCell id="rds" value="RDS Database&#xa;MySQL" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;" vertex="1" parent="vpc">
          <mxGeometry x="300" y="100" width="48" height="48" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

# Invalid XML samples for testing error handling
INVALID_XML_NO_MXFILE = '''<diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
</diagram>'''

INVALID_XML_NO_CLOSING_MXFILE = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
      </root>
    </mxGraphModel>
  </diagram>'''

INVALID_XML_NO_MXGRAPHMODEL = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <root>
      <mxCell id="0"/>
    </root>
  </diagram>
</mxfile>'''

INVALID_XML_NO_ROOT = '''<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel>
      <mxCell id="0"/>
    </mxGraphModel>
  </diagram>
</mxfile>'''

# Claude API response samples
CLAUDE_RESPONSE_WITH_CODE_BLOCK = f'''Here's your Draw.io diagram:

```xml
{MINIMAL_VALID_XML}
```

This diagram should work for your needs.'''

CLAUDE_RESPONSE_DIRECT_XML = MINIMAL_VALID_XML

CLAUDE_RESPONSE_NO_XML = "I cannot create a diagram for this request. Please provide more specific requirements."

CLAUDE_RESPONSE_INVALID_XML = '''Here's your diagram:

```xml
<invalid>This is not valid Draw.io XML</invalid>
```'''