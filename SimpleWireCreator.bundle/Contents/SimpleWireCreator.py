# Wire Creator Add-in for Fusion 360
# Creates wires/cables between two profiles using loft with spline centerline

import adsk.core
import adsk.fusion
import traceback
import math
import os

handlers = []

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the path to the Resources folder for icons
        resourceFolder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Resources')
        
        cmdDef = ui.commandDefinitions.itemById('WireCreatorCommand')
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                'WireCreatorCommand',
                'Simple Wire Creator',
                'Create a wire/cable between two edges or faces',
                resourceFolder
            )
        
        onCommandCreated = WireCreatorCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if addInsPanel:
            buttonControl = addInsPanel.controls.itemById('WireCreatorCommand')
            if not buttonControl:
                addInsPanel.controls.addCommand(cmdDef)
        
    except:
        if ui:
            ui.messageBox('Failed to start Simple Wire Creator:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if addInsPanel:
            buttonControl = addInsPanel.controls.itemById('WireCreatorCommand')
            if buttonControl:
                buttonControl.deleteMe()
        
        cmdDef = ui.commandDefinitions.itemById('WireCreatorCommand')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        pass


class WireCreatorCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            # First Profile selection
            sel1 = inputs.addSelectionInput(
                'profileSelection1',
                'First Profile',
                'Select the first edge or face'
            )
            sel1.addSelectionFilter('Edges')
            sel1.addSelectionFilter('Faces')
            sel1.setSelectionLimits(1, 1)
            
            # Flip direction for first profile
            flip1 = inputs.addBoolValueInput(
                'flipDirection1',
                'Flip',
                True,
                '',
                False
            )
            
            # Second Profile selection
            sel2 = inputs.addSelectionInput(
                'profileSelection2', 
                'Second Profile',
                'Select the second edge or face'
            )
            sel2.addSelectionFilter('Edges')
            sel2.addSelectionFilter('Faces')
            sel2.setSelectionLimits(1, 1)
            
            # Flip direction for second profile
            flip2 = inputs.addBoolValueInput(
                'flipDirection2',
                'Flip',
                True,
                '',
                False
            )
            # Midpoint count button row (horizontal, 1, 2, or 3)
            resourceFolder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Resources')
            midpointRow = inputs.addButtonRowCommandInput(
                'midpointCount',
                'Spline Midpoints',
                False  # isMultiSelectEnabled = False for single selection
            )
            midpointRow.listItems.add('1', True, os.path.join(resourceFolder, 'midpoint_1'))
            midpointRow.listItems.add('2', False, os.path.join(resourceFolder, 'midpoint_2'))
            midpointRow.listItems.add('3', False, os.path.join(resourceFolder, 'midpoint_3'))

            # Midpoints Offset spinner (0-1000mm, default 3mm, step 1mm)
            offsetSpinner = inputs.addFloatSpinnerCommandInput(
                'droopAmount',
                'Midpoints Offset',
                'mm',
                0,     # min 0mm
                1000,  # max 1000mm
                1,     # step 1mm
                3      # default 3mm
            )
            
            # Invert Offset checkbox
            invertCheck = inputs.addBoolValueInput('invertOffset', 'Invert Offset', True, '', False)
            
            # Endpoints Strength spinner (1-50%, default 5%, step 5%)
            endpointSpinner = inputs.addFloatSpinnerCommandInput(
                'handleStrength',
                'Endpoints Strength',
                '',    # No units (percentage)
                1,     # min 1%
                50,    # max 50%
                5,     # step 5%
                5      # default 5%
            )
            
            # Inherit Appearance checkbox
            inheritCheck = inputs.addBoolValueInput('inheritAppearance', 'Inherit Appearance', True, '', False)
            
            # Tint Color dropdown
            tintDropdown = inputs.addDropDownCommandInput(
                'tintColor',
                'Tint Color',
                adsk.core.DropDownStyles.LabeledIconDropDownStyle
            )
            tintItems = tintDropdown.listItems
            tintItems.add('None', True)
            tintItems.add('Black', False)
            tintItems.add('White', False)
            tintItems.add('Red', False)
            tintItems.add('Blue', False)
            tintItems.add('Green', False)
            tintItems.add('Yellow', False)
            tintItems.add('Orange', False)
            tintItems.add('Brown', False)
            tintItems.add('Grey', False)
            tintItems.add('Pink', False)
            
            onExecute = WireCreatorExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            onPreview = WireCreatorPreviewHandler()
            cmd.executePreview.add(onPreview)
            handlers.append(onPreview)
            
            onInputChanged = WireCreatorInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
            
            # Add activate handler to check initial selection
            onActivate = WireCreatorActivateHandler()
            cmd.activate.add(onActivate)
            handlers.append(onActivate)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class WireCreatorInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            changedInput = args.input
            inputs = args.inputs
            
            # When first profile is selected, move focus to second
            if changedInput.id == 'profileSelection1':
                sel1 = inputs.itemById('profileSelection1')
                sel2 = inputs.itemById('profileSelection2')
                if sel1.selectionCount == 1 and sel2.selectionCount == 0:
                    sel2.hasFocus = True
        except:
            pass


class WireCreatorActivateHandler(adsk.core.CommandEventHandler):
    """Handler for when the command activates."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        # No auto-advance on activate - just let Fusion handle it
        pass


class WireCreatorPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs
            
            sel1Input = inputs.itemById('profileSelection1')
            sel2Input = inputs.itemById('profileSelection2')
            droopInput = inputs.itemById('droopAmount')
            flip1Input = inputs.itemById('flipDirection1')
            flip2Input = inputs.itemById('flipDirection2')
            midpointInput = inputs.itemById('midpointCount')
            handleInput = inputs.itemById('handleStrength')
            invertInput = inputs.itemById('invertOffset')
            inheritInput = inputs.itemById('inheritAppearance')
            tintInput = inputs.itemById('tintColor')
            
            if sel1Input.selectionCount == 0 or sel2Input.selectionCount == 0:
                return
            
            entity1 = sel1Input.selection(0).entity
            entity2 = sel2Input.selection(0).entity
            
            # Get offset value from spinner
            droopValue = droopInput.value
            
            # Apply invert if checked
            if invertInput and invertInput.value:
                droopValue = -droopValue
            
            flip1 = flip1Input.value
            flip2 = flip2Input.value
            
            # Get midpoint count from radio buttons
            midpointCount = 1
            if midpointInput:
                selectedItem = midpointInput.selectedItem
                if selectedItem:
                    midpointCount = int(selectedItem.name)
            
            # Get endpoints strength (percentage)
            handleStrength = 5.0
            if handleInput:
                handleStrength = handleInput.value
            
            # Get appearance inputs
            useInherit = inheritInput.value if inheritInput else True
            tintColorName = tintInput.selectedItem.name if tintInput and tintInput.selectedItem else 'None'
            
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            comp = design.activeComponent
            
            createWire(comp, entity1, entity2, droopValue, flip1, flip2, midpointCount, handleStrength, None, isPreview=True, useInherit=useInherit, tintColorName=tintColorName)
            eventArgs.isValidResult = True
            
        except:
            pass


class WireCreatorExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = adsk.fusion.Design.cast(app.activeProduct)
            
            if not design:
                ui.messageBox('Please open a design first.')
                return
            
            inputs = args.command.commandInputs
            
            sel1Input = inputs.itemById('profileSelection1')
            sel2Input = inputs.itemById('profileSelection2')
            droopInput = inputs.itemById('droopAmount')
            flip1Input = inputs.itemById('flipDirection1')
            flip2Input = inputs.itemById('flipDirection2')
            midpointInput = inputs.itemById('midpointCount')
            handleInput = inputs.itemById('handleStrength')
            invertInput = inputs.itemById('invertOffset')
            inheritInput = inputs.itemById('inheritAppearance')
            tintInput = inputs.itemById('tintColor')
            
            if sel1Input.selectionCount == 0 or sel2Input.selectionCount == 0:
                ui.messageBox('Please select both profiles.')
                return
            
            entity1 = sel1Input.selection(0).entity
            entity2 = sel2Input.selection(0).entity
            
            # Get offset value from spinner
            droopValue = droopInput.value
            
            # Apply invert if checked
            if invertInput and invertInput.value:
                droopValue = -droopValue
            
            flip1 = flip1Input.value
            flip2 = flip2Input.value
            
            # Get midpoint count from radio buttons
            midpointCount = 1
            if midpointInput:
                selectedItem = midpointInput.selectedItem
                if selectedItem:
                    midpointCount = int(selectedItem.name)
            
            # Get endpoints strength (percentage)
            handleStrength = 5.0
            if handleInput:
                handleStrength = handleInput.value
            
            # Get appearance inputs
            useInherit = inheritInput.value if inheritInput else True
            tintColorName = tintInput.selectedItem.name if tintInput and tintInput.selectedItem else 'None'
            
            comp = design.activeComponent
            createWire(comp, entity1, entity2, droopValue, flip1, flip2, midpointCount, handleStrength, ui, isPreview=False, useInherit=useInherit, tintColorName=tintColorName)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def getProfileInfo(entity):
    """
    Get center point and normal for an edge or face.
    For circular edges: uses circle center/normal
    For cylindrical faces: finds the circular edge and uses its center
    For planar faces: uses the face centroid
    Returns: (center, normal, loftEntity, constraintFace)
    """
    center = None
    normal = None
    loftEntity = entity
    constraintFace = None
    
    if isinstance(entity, adsk.fusion.BRepEdge):
        edge = entity
        geom = edge.geometry
        
        if isinstance(geom, adsk.core.Circle3D):
            center = geom.center.copy()
            normal = geom.normal.copy()
        elif isinstance(geom, adsk.core.Ellipse3D):
            center = geom.center.copy()
            normal = geom.normal.copy()
        else:
            # For other edge types, use midpoint
            evaluator = edge.evaluator
            _, startParam, endParam = evaluator.getParameterExtents()
            midParam = (startParam + endParam) / 2
            _, center = evaluator.getPointAtParameter(midParam)
            
            # Get normal from adjacent planar face
            normal = adsk.core.Vector3D.create(0, 0, 1)
            for face in edge.faces:
                if isinstance(face.geometry, adsk.core.Plane):
                    normal = face.geometry.normal.copy()
                    break
        
        # Find constraint face (planar face adjacent to edge)
        for face in edge.faces:
            if isinstance(face.geometry, adsk.core.Plane):
                constraintFace = face
                break
    
    elif isinstance(entity, adsk.fusion.BRepFace):
        face = entity
        
        if isinstance(face.geometry, adsk.core.Plane):
            # Planar face - get centroid using bounding box
            bbox = face.boundingBox
            center = adsk.core.Point3D.create(
                (bbox.minPoint.x + bbox.maxPoint.x) / 2,
                (bbox.minPoint.y + bbox.maxPoint.y) / 2,
                (bbox.minPoint.z + bbox.maxPoint.z) / 2
            )
            normal = face.geometry.normal.copy()
            constraintFace = face
            
        elif isinstance(face.geometry, adsk.core.Cylinder):
            # Cylindrical face - find a circular edge to get the center
            cyl = face.geometry
            normal = cyl.axis.copy()
            
            # Find a circular edge on this face
            for edge in face.edges:
                if isinstance(edge.geometry, adsk.core.Circle3D):
                    circle = edge.geometry
                    center = circle.center.copy()
                    loftEntity = edge  # Use the edge for loft, not the face
                    break
            
            if not center:
                # Fallback: use face evaluator
                _, center = face.evaluator.getPointAtParameter(adsk.core.Point2D.create(0.5, 0.5))
        
        elif isinstance(face.geometry, adsk.core.Cone):
            # Conical face
            cone = face.geometry
            normal = cone.axis.copy()
            
            for edge in face.edges:
                if isinstance(edge.geometry, adsk.core.Circle3D):
                    circle = edge.geometry
                    center = circle.center.copy()
                    loftEntity = edge
                    break
            
            if not center:
                _, center = face.evaluator.getPointAtParameter(adsk.core.Point2D.create(0.5, 0.5))
        
        else:
            # Other face types
            _, center = face.evaluator.getPointAtParameter(adsk.core.Point2D.create(0.5, 0.5))
            _, normal = face.evaluator.getNormalAtPoint(center)
            if normal:
                normal = normal.copy()
    
    # Return copies to ensure independence
    if center and hasattr(center, 'copy'):
        center = center.copy()
    if normal and hasattr(normal, 'copy'):
        normal = normal.copy()
    
    return center, normal, loftEntity, constraintFace


def applyAppearance(body, useInherit, tintColorName, sourceAppearance):
    """Apply an appearance or custom color to a body with support for inheritance and tinting."""
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            return

        # If inheritance is off and no tint is selected, do nothing (keep default)
        if not useInherit and tintColorName == 'None':
            return

        finalAppearance = None
        baseAppearance = None

        if useInherit and sourceAppearance:
            baseAppearance = sourceAppearance
        elif tintColorName != 'None':
            # Search for a neutral base material (ABS White ideally)
            # Try a few common template names for a neutral base
            templateNames = [
                'ABS (White)', 
                'Plastic - Matte (White)', 
                'Plastic - Glossy (White)', 
                'Paint - Enamel Glossy (White)'
            ]
            
            # Known modern Fusion library name and some fallbacks
            libNames = ['Fusion Appearance Library', 'Fusion 360 Appearance Library']
            
            for libName in libNames:
                lib = app.materialLibraries.itemByName(libName)
                if lib:
                    for tName in templateNames:
                        baseAppearance = lib.appearances.itemByName(tName)
                        if baseAppearance: break
                if baseAppearance: break
            
            # Fallback to any library if still not found
            if not baseAppearance:
                for lib in app.materialLibraries:
                    for tName in templateNames:
                        baseAppearance = lib.appearances.itemByName(tName)
                        if baseAppearance: break
                    if baseAppearance: break

        if tintColorName != 'None' and baseAppearance:
            # Define tint colors (RGB) - Realistic insulation colors
            tintColors = {
                'Black': (25, 25, 25),
                'White': (235, 235, 235),
                'Red': (190, 30, 30),
                'Blue': (0, 85, 175),
                'Green': (40, 140, 50),
                'Yellow': (250, 200, 0),
                'Orange': (240, 100, 0),
                'Brown': (110, 60, 30),
                'Grey': (110, 110, 110),
                'Pink': (230, 100, 160)
            }
            
            if tintColorName in tintColors:
                # Create a unique name for the tinted appearance
                # If we're not inheriting, we don't want to prefix with the source material name necessarily,
                # but for simplicity we'll use the base name.
                newAppearanceName = 'Wire_' + tintColorName
                if useInherit and sourceAppearance:
                    newAppearanceName = sourceAppearance.name + "_" + tintColorName
                
                # Check if it already exists in the design
                finalAppearance = design.appearances.itemByName(newAppearanceName)
                
                if not finalAppearance:
                    # Clone the base appearance
                    finalAppearance = design.appearances.addByCopy(baseAppearance, newAppearanceName)
                    
                    # Try to find the color property to change
                    colorPropNames = ['Color', 'reflectance_color', 'base_color']
                    colorProp = None
                    for pName in colorPropNames:
                        colorProp = finalAppearance.appearanceProperties.itemByName(pName)
                        if colorProp: break
                    
                    if colorProp:
                        r, g, b = tintColors[tintColorName]
                        colorProp = adsk.core.ColorProperty.cast(colorProp)
                        if colorProp:
                            colorProp.value = adsk.core.Color.create(r, g, b, 255)
        elif useInherit:
            # No tint, just inherit
            finalAppearance = baseAppearance

        if finalAppearance:
            body.appearance = finalAppearance
            
    except:
        pass


def createWire(comp, entity1, entity2, droopAmount, flipDir1, flipDir2, midpointCount, handleStrength, ui, isPreview=False, useInherit=True, tintColorName='None'):
    """Create a wire between two profiles with configurable midpoints and handle strength."""
    try:
        # Get geometry info
        center1, normal1, loftEntity1, face1 = getProfileInfo(entity1)
        center2, normal2, loftEntity2, face2 = getProfileInfo(entity2)
        
        if not center1 or not center2:
            if ui:
                ui.messageBox('Could not extract geometry.')
            return
        
        if not normal1 or not normal2:
            if ui:
                ui.messageBox('Could not determine normals.')
            return
        
        # Calculate wire vector
        wireVec = adsk.core.Vector3D.create(
            center2.x - center1.x,
            center2.y - center1.y,
            center2.z - center1.z
        )
        wireLength = wireVec.length
        
        if wireLength < 0.0001:
            if ui:
                ui.messageBox('Profiles are too close.')
            return
        
        wireDir = wireVec.copy()
        wireDir.normalize()
        
        # Determine if each entity is a face or edge for normal handling
        isFace1 = isinstance(entity1, adsk.fusion.BRepFace)
        isFace2 = isinstance(entity2, adsk.fusion.BRepFace)
        
        # For EDGES: Edge1 points up, Edge2 use natural direction
        # For FACES: Face1 natural, Face2 flipped
        
        if not isFace1:
            # Edge1: flip it
            normal1 = adsk.core.Vector3D.create(-normal1.x, -normal1.y, -normal1.z)
        # Face1: keep as-is
        
        if isFace2:
            # Face2: flip it
            normal2 = adsk.core.Vector3D.create(-normal2.x, -normal2.y, -normal2.z)
        # Edge2: keep as-is (natural direction)
        
        # Apply user flip on top
        if flipDir1:
            normal1 = adsk.core.Vector3D.create(-normal1.x, -normal1.y, -normal1.z)
        
        if flipDir2:
            normal2 = adsk.core.Vector3D.create(-normal2.x, -normal2.y, -normal2.z)
        
        # Calculate offset using trigonometry based on normal alignment
        # Note: When profiles both point "up", their normals actually point OPPOSITE
        # (one exits up, one exits down toward the wire), so dot = -1 means "aligned"
        normalDot = normal1.dotProduct(normal2)
        
        # Scale factor: 1 when normals opposite (dot=-1), 0 when same (dot=1)
        # Formula: (1 - dot) / 2 swaps the behavior
        alignmentFactor = (1.0 - normalDot) / 2.0
        
        # Calculate offset direction from summed normals
        sumNormal = adsk.core.Vector3D.create(
            normal1.x + normal2.x,
            normal1.y + normal2.y,
            normal1.z + normal2.z
        )
        
        # Project summed normal perpendicular to wire direction
        dotWire = sumNormal.dotProduct(wireDir)
        droopDir = adsk.core.Vector3D.create(
            sumNormal.x - dotWire * wireDir.x,
            sumNormal.y - dotWire * wireDir.y,
            sumNormal.z - dotWire * wireDir.z
        )
        
        # Normalize the direction
        if droopDir.length > 0.0001:
            droopDir.normalize()
        else:
            # Fallback to world up if normals cancel out
            worldUp = adsk.core.Vector3D.create(0, 0, 1)
            if abs(wireDir.z) > 0.9:
                worldUp = adsk.core.Vector3D.create(0, 1, 0)
            dotUp = worldUp.dotProduct(wireDir)
            droopDir = adsk.core.Vector3D.create(
                worldUp.x - dotUp * wireDir.x,
                worldUp.y - dotUp * wireDir.y,
                worldUp.z - dotUp * wireDir.z
            )
            if droopDir.length > 0.0001:
                droopDir.normalize()
            else:
                droopDir = adsk.core.Vector3D.create(0, 0, 1)
        
        # Apply scaled offset: full amount when aligned, zero when opposite
        scaledOffset = droopAmount * alignmentFactor
        
        # Generate evenly distributed midpoints along the wire
        # Midpoints are placed at equal intervals between center1 and center2
        midPoints = []
        for i in range(midpointCount):
            # Calculate parameter t for this midpoint (evenly spaced)
            # For 1 midpoint: t = 0.5
            # For 2 midpoints: t = 0.333, 0.667
            # For 3 midpoints: t = 0.25, 0.5, 0.75
            t = (i + 1) / (midpointCount + 1)
            
            # Linear interpolation for base position
            baseX = center1.x + (center2.x - center1.x) * t
            baseY = center1.y + (center2.y - center1.y) * t
            baseZ = center1.z + (center2.z - center1.z) * t
            
            # Apply full offset to all midpoints
            midPoint = adsk.core.Point3D.create(
                baseX + droopDir.x * scaledOffset,
                baseY + droopDir.y * scaledOffset,
                baseZ + droopDir.z * scaledOffset
            )
            midPoints.append(midPoint)
        
        # Create 3D sketch
        sketches = comp.sketches
        xyPlane = comp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        sketch.name = "WireCreator_Spline"
        sketch.is3D = True
        
        # Transform points to sketch local coordinates
        sketchTransform = sketch.transform
        sketchTransformInv = sketchTransform.copy()
        sketchTransformInv.invert()
        
        localCenter1 = center1.copy()
        localCenter1.transformBy(sketchTransformInv)
        
        localCenter2 = center2.copy()
        localCenter2.transformBy(sketchTransformInv)
        
        # Also transform normals for tangent positioning
        localNormal1 = normal1.copy()
        localNormal1.transformBy(sketchTransformInv)
        localNormal1.normalize()
        
        localNormal2 = normal2.copy()
        localNormal2.transformBy(sketchTransformInv)
        localNormal2.normalize()
        
        # Transform midpoints to sketch local coordinates
        localMidPoints = []
        for mp in midPoints:
            localMp = mp.copy()
            localMp.transformBy(sketchTransformInv)
            localMidPoints.append(localMp)
        
        # Create fitted spline (passes through all points)
        points = adsk.core.ObjectCollection.create()
        points.add(localCenter1)
        for localMp in localMidPoints:
            points.add(localMp)
        points.add(localCenter2)
        
        spline = sketch.sketchCurves.sketchFittedSplines.add(points)
        
        if not spline:
            if ui:
                ui.messageBox('Failed to create spline.')
            return
        
        # Set tangent handles only for endpoints (controlled by Handle Strength slider)
        # Let Fusion auto-calculate midpoint tangents for naturally smooth curves
        try:
            fitPoints = spline.fitPoints
            if fitPoints.count >= 2:
                firstFitPoint = fitPoints.item(0)
                lastFitPoint = fitPoints.item(fitPoints.count - 1)
                
                # Activate tangent handles for endpoints only
                tangentLine1 = spline.activateTangentHandle(firstFitPoint)
                tangentLine2 = spline.activateTangentHandle(lastFitPoint)
                
                # Calculate tangent length from handle strength (percentage of wire length)
                tangentLength = wireLength * (handleStrength / 100.0)
                tangentLength = max(tangentLength, 0.05)  # minimum 0.05cm = 0.5mm
                
                if tangentLine1:
                    newEndPoint = adsk.core.Point3D.create(
                        localCenter1.x + localNormal1.x * tangentLength,
                        localCenter1.y + localNormal1.y * tangentLength,
                        localCenter1.z + localNormal1.z * tangentLength
                    )
                    try:
                        tangentLine1.endSketchPoint.move(
                            adsk.core.Vector3D.create(
                                newEndPoint.x - tangentLine1.endSketchPoint.geometry.x,
                                newEndPoint.y - tangentLine1.endSketchPoint.geometry.y,
                                newEndPoint.z - tangentLine1.endSketchPoint.geometry.z
                            )
                        )
                    except:
                        pass
                
                if tangentLine2:
                    newEndPoint = adsk.core.Point3D.create(
                        localCenter2.x + localNormal2.x * tangentLength,
                        localCenter2.y + localNormal2.y * tangentLength,
                        localCenter2.z + localNormal2.z * tangentLength
                    )
                    try:
                        tangentLine2.endSketchPoint.move(
                            adsk.core.Vector3D.create(
                                newEndPoint.x - tangentLine2.endSketchPoint.geometry.x,
                                newEndPoint.y - tangentLine2.endSketchPoint.geometry.y,
                                newEndPoint.z - tangentLine2.endSketchPoint.geometry.z
                            )
                        )
                    except:
                        pass
        except:
            pass
        
        
        # Create loft
        loftFeats = comp.features.loftFeatures
        loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        loftInput.loftSections.add(loftEntity1)
        loftInput.loftSections.add(loftEntity2)
        loftInput.centerLineOrRails.addCenterLine(spline)
        loftInput.isSolid = True
        
        try:
            loftFeat = loftFeats.add(loftInput)
            if loftFeat:
                # Determine source appearance if needed
                sourceAppearance = None
                try:
                    if hasattr(entity1, 'appearance') and entity1.appearance:
                        sourceAppearance = entity1.appearance
                    elif hasattr(entity1, 'body') and entity1.body.appearance:
                        sourceAppearance = entity1.body.appearance
                except:
                    pass

                # Apply appearance to the resulting body
                if loftFeat.bodies.count > 0:
                    applyAppearance(loftFeat.bodies.item(0), useInherit, tintColorName, sourceAppearance)
            elif ui and not isPreview:
                ui.messageBox('Loft failed.')
        except Exception as e:
            if ui and not isPreview:
                ui.messageBox('Loft error: {}'.format(str(e)))
        
    except:
        if ui:
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))
