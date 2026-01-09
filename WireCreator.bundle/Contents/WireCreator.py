# Wire Creator Add-in for Fusion 360
# Creates wires/cables between two profiles using loft with spline centerline

import adsk.core
import adsk.fusion
import traceback
import math

handlers = []

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmdDef = ui.commandDefinitions.itemById('WireCreatorCommand')
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                'WireCreatorCommand',
                'Wire Creator',
                'Create a wire/cable between two edges or faces',
                ''
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
            ui.messageBox('Failed to start Wire Creator:\n{}'.format(traceback.format_exc()))


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
            
            # Center point offset (formerly "Wire Droop")
            offsetInput = inputs.addValueInput(
                'droopAmount',
                'Center Point Offset',
                'mm',
                adsk.core.ValueInput.createByReal(0.3)
            )
            
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
            
            if sel1Input.selectionCount == 0 or sel2Input.selectionCount == 0:
                return
            
            entity1 = sel1Input.selection(0).entity
            entity2 = sel2Input.selection(0).entity
            
            # Get offset value (can be negative)
            droopValue = droopInput.value
            flip1 = flip1Input.value
            flip2 = flip2Input.value
            
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            comp = design.activeComponent
            
            createWire(comp, entity1, entity2, droopValue, flip1, flip2, None, isPreview=True)
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
            
            if sel1Input.selectionCount == 0 or sel2Input.selectionCount == 0:
                ui.messageBox('Please select both profiles.')
                return
            
            entity1 = sel1Input.selection(0).entity
            entity2 = sel2Input.selection(0).entity
            
            # Get offset value (can be negative)
            droopValue = droopInput.value
            flip1 = flip1Input.value
            flip2 = flip2Input.value
            
            comp = design.activeComponent
            createWire(comp, entity1, entity2, droopValue, flip1, flip2, ui, isPreview=False)
            
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


def createWire(comp, entity1, entity2, droopAmount, flipDir1, flipDir2, ui, isPreview=False):
    """Create a wire between two profiles."""
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
        
        # Calculate midpoint
        midX = (center1.x + center2.x) / 2
        midY = (center1.y + center2.y) / 2
        midZ = (center1.z + center2.z) / 2
        
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
        
        midPoint = adsk.core.Point3D.create(
            midX + droopDir.x * scaledOffset,
            midY + droopDir.y * scaledOffset,
            midZ + droopDir.z * scaledOffset
        )
        
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
        
        localMidPoint = midPoint.copy()
        localMidPoint.transformBy(sketchTransformInv)
        
        localCenter2 = center2.copy()
        localCenter2.transformBy(sketchTransformInv)
        
        # Also transform normals for tangent positioning
        localNormal1 = normal1.copy()
        localNormal1.transformBy(sketchTransformInv)
        localNormal1.normalize()
        
        localNormal2 = normal2.copy()
        localNormal2.transformBy(sketchTransformInv)
        localNormal2.normalize()
        
        # Create spline
        points = adsk.core.ObjectCollection.create()
        points.add(localCenter1)
        points.add(localMidPoint)
        points.add(localCenter2)
        
        spline = sketch.sketchCurves.sketchFittedSplines.add(points)
        
        if not spline:
            if ui:
                ui.messageBox('Failed to create spline.')
            return
        
        # Set tangent handles to be perpendicular to the faces
        # by explicitly positioning the tangent handle endpoints
        try:
            fitPoints = spline.fitPoints
            if fitPoints.count >= 2:
                firstFitPoint = fitPoints.item(0)
                lastFitPoint = fitPoints.item(fitPoints.count - 1)
                
                # Activate tangent handles
                tangentLine1 = spline.activateTangentHandle(firstFitPoint)
                tangentLine2 = spline.activateTangentHandle(lastFitPoint)
                
                # Calculate desired tangent handle endpoints
                # Tangent handle length = 1/3 of the droop (minimum 0.05cm = 0.5mm)
                tangentLength = max(abs(droopAmount) / 3, 0.05)
                
                if tangentLine1:
                    # Move the outer endpoint of the tangent line along normal1
                    # The tangent line goes from the fit point to the handle
                    # We want the handle to point along normal1
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
                    # For the second tangent, normal2 points toward center1, so use it directly
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
                
                # Also try to add perpendicular constraints as backup
                constraints = sketch.geometricConstraints
                if tangentLine1 and face1:
                    try:
                        constraints.addPerpendicular(tangentLine1, face1)
                    except:
                        pass
                if tangentLine2 and face2:
                    try:
                        constraints.addPerpendicular(tangentLine2, face2)
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
            if not loftFeat and ui and not isPreview:
                ui.messageBox('Loft failed.')
        except Exception as e:
            if ui and not isPreview:
                ui.messageBox('Loft error: {}'.format(str(e)))
        
    except:
        if ui:
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))
