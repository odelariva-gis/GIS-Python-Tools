# -*- coding: utf-8 -*-

import arcpy, os
from arcpy import env


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Elevation Adjuster Tool"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [PoiAdjust, LineAdjust]


class PoiAdjust(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "POI Elevation Adjust Tool"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
             displayName="POI's/Units To Adjust",
             name="poi_fc",
             datatype="GPFeatureLayer",
             parameterType="Required",
             direction="Input") 
    

        param1 = arcpy.Parameter(
             displayName="Select to Adjust Height to Field (Optional)",
             name="adjust_height",
             datatype="GPBoolean",
             parameterType="Optional",
             direction="Input")


        param2 = arcpy.Parameter(
             displayName="Relative Elevation Field",
             name="relative_elevation_field",
             datatype="Field",
             parameterType="Optional",
             direction="Input")

        param2.filter.list = ['Double']
        param2.parameterDependencies = ['poi_fc']
        param2.enabled = False
        params = [param0, param1, param2]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        if parameters[1].value:
            if parameters[1].value is not None:
                parameters[2].enabled = True
      

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if parameters[1].value is not None and parameters[2].value is None:
            parameters[2].setErrorMessage("Please set your height field...")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.outputZFlag = "Enabled"
        arcpy.env.outputMFlag = "Same AS Input"
        env.overwriteOutput = True

        poi_fc                    = parameters[0].valueAsText
        adjust_height             = parameters[1].value
        relative_elevation_field  = parameters[2].valueAsText

        desc = arcpy.Describe(poi_fc)

        if desc.shapeType == 'Polygon' or desc.shapeType == 'Point':
            if adjust_height == None:
                adjust_height = False

            self.get_message("Boolean value: "  + str(adjust_height))

            if adjust_height:
                self.get_message("Will adjust vertical elevation to field...")

            self.get_message("Adding Z mean for " + poi_fc + " feature class...") 

            if desc.shapeType == "Point":   
                arcpy.ddd.AddZInformation(poi_fc, "Z","" )
            elif desc.shapeType == "Polygon":
                arcpy.ddd.AddZInformation(poi_fc, "Z_MEAN","" )

            self.get_message("Checking for existing field...")

            list_fields = arcpy.ListFields(poi_fc)

            for field in list_fields:
                if field.name == "Neg_Z":
                    arcpy.management.DeleteField(poi_fc, "Neg_Z")
                    self.get_message("Neg Z existed and will be deleted.")
                else:
                    pass

            self.get_message("Creating negative Z information for " + poi_fc + " feature class.")
            arcpy.management.AddField(poi_fc, "Neg_Z", "DOUBLE", "", "", "","Negative Z", "","","")

            if desc.shapeType == "Point":   
                with arcpy.da.UpdateCursor(poi_fc,["Z","Neg_Z"]) as cursor:
                    for row in cursor:
                        if row[0] is None:
                            pass
                        else:
                            row[1] = row[0] * -1
                            cursor.updateRow(row)
                    del cursor
            elif desc.shapeType == "Polygon":
                with arcpy.da.UpdateCursor(poi_fc,["Z_MEAN","Neg_Z"]) as cursor:
                    for row in cursor:
                        if row[0] is None:
                            pass
                        else:
                            row[1] = row[0] * -1
                            cursor.updateRow(row)
                    del cursor

            arcpy.management.Adjust3DZ(poi_fc, "NO_REVERSE", "Neg_Z","","" )

            self.get_message("Finished fixing Z data.") 

            if adjust_height:
                arcpy.management.Adjust3DZ(poi_fc, "NO_REVERSE", relative_elevation_field, "", "")
                
            else: 
                self.get_message("Will not adjust elevation. All features will be set to ground.")

            ### Delete extra fields here
            arcpy.management.DeleteField(poi_fc, ['Z_MEAN', 'Neg_Z'], 'DELETE_FIELDS')

        else:
            arcpy.AddError("Tool can only process Polygons or Points. Tool will exit now!")

        return
    

class LineAdjust(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Polyline Elevation Adjust Tool"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Polyline Feature Class to Adjust",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input") 

        param1 = arcpy.Parameter(
            displayName="Relative Elevation Field",
            name="relative_elevation_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")

        param1.filter.list = ['Double']
        param1.parameterDependencies = ['in_fc']
        param1.enabled = True

        params = [param0, param1]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # if parameters[1].value:
        #     if parameters[1].value is not None:
        #         parameters[2].enabled = True
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # if parameters[1].value is not None and parameters[2].value is None:
        #     parameters[2].setErrorMessage("Please set your height field...")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.outputZFlag = "Enabled"
        arcpy.env.outputMFlag = "Same AS Input"
        env.overwriteOutput = True

        in_fc                    = parameters[0].valueAsText
        relative_elevation_field  = parameters[1].valueAsText

        desc = arcpy.Describe(in_fc)

        shape_field_name = desc.ShapeFieldName
        shape_field_z = shape_field_name + '@'

        self.get_message(f'')

        if desc.shapeType == 'Polyline':
          
            self.get_message(f"Adjusting your {desc.shapeType} to relative elevation...")

            with arcpy.da.UpdateCursor(in_fc, [shape_field_z, relative_elevation_field]) as cursor:
                for row in cursor:
                    coords = row[0]
                    new_geo = arcpy.Array()
                    for part in coords: 

                        new_part = arcpy.Array()
                        num_segs = len(part)

                        _step = 1
                        self.get_message(f'Length of my part is: {num_segs}')
                        self.get_message('Iterating through the vertices...')
                        self.get_message(" "*50)            
                        new_part = arcpy.Array()

                        for pnt in part:
                            if pnt:            
                                new_point = arcpy.Point(pnt.X, pnt.Y, row[1])
                                new_part.add(new_point)      
                    
                    ### This is where the geometry gets added will needed 
                    new_geo.add(new_part)
                    new_shape = arcpy.Polyline(new_geo, None, True)
                    self.get_message(f'NEW SHAPE: {new_shape}')
                    self.get_message(f'NEW SHAPE TYPE: {new_shape.type}')
                    
                    ### This updates the actual feature class 
                    if new_shape is not None: 
                        row = [new_shape, row[1]]
                        cursor.updateRow(row)
                self.get_message("Finished adjusting vertices...")
            
        else:
            arcpy.AddError("Tool can only process Polylines. Tool will exit now!")

        self.get_message("Tool has succesfully completed running!")

        return

    ### Get messages funcion. 
    def get_message(self, message):
        arcpy.AddMessage(message)