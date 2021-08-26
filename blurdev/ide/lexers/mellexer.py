##
#   :namespace  python.blurdev.ide.lexers.mellexer
#
#   :remarks    A lexer for Maya Mel scripts
#
#   :author     mikeh@blur.com
#   :author     Blur Studio
#   :date       10/03/14
#

from __future__ import absolute_import
import re
from Qt.Qsci import QsciLexerCPP
from Qt.QtGui import QColor

MEL_SYNTAX = """and array as case catch continue do else exit float for from global if
in int local not of off on or proc random return select string then throw to try vector
when where while with true false
"""

# Generated by the following code
# import maya.cmds as cmds
# print(' '.join(cmds.help( '[a-z]*', list=True )))
MEL_KEYWORDS = """window aaf2fcp about abs acos acosd acosh addAttr addDynamic
addExtension addIK2BsolverCallbacks addMetadata addPP adskAsset adskAssetLibrary
adskAssetList adskAssetListUI adskRepresentation affectedNet affects agFormatIn
agFormatOut aimConstraint air aliasAttr align alignCtx alignCurve alignSurface
allNodeTypes ambientLight aminocompound angle angleBetween animCurveEditor animDisplay
animLayer animView annotate apfEntityNode applicationcomplex applyAttrPattern
applyMetadata applyTake arcLenDimContext arcLengthDimension arclen arrayMapper
art3dPaintCtx artAttr artAttrCtx artAttrPaintVertexCtx artAttrSkinPaint
artAttrSkinPaintCmd artAttrSkinPaintCtx artAttrTool artBaseCtx artBuildPaintMenu
artFluidAttr artFluidAttrCtx artPuttyCtx artSelect artSelectCtx artSetPaint
artSetPaintCtx artUserPaintCtx asin asind asinh assembly assignCommand assignInputDevice
assignViewportFactories atan atan2 atan2d atand atanh attachCurve attachDeviceAttr
attachFluidCache attachGeometryCache attachNclothCache attachSurface attrColorSliderGrp
attrCompatibility attrControlGrp attrEnumOptionMenu attrEnumOptionMenuGrp attrFieldGrp
attrFieldSliderGrp attrNavigationControlGrp attributeInfo attributeMenu attributeName
attributeQuery audioTrack autoKeyframe autoPlace autoSave bakeClip bakePartialHistory
bakeResults bakeSimulation baseTemplate baseView batchRender besselj0 besselj1 besseljn
besselyn bevel bevelPlus bezierAnchorPreset bezierAnchorState bezierCurveToNurbs
bezierInfo bifrost bifrostCreateMayaView bifrostproject binMembership bindSkin blend
blend2 blendCtx blendShape blendShapeEditor blendShapePanel blendTwoAttr blindDataType
blocksize boneLattice boundary boxDollyCtx boxZoomCtx bufferCurve buildBookmarkMenu
buildKeyframeMenu buildSendToBackburnerDialog button buttonManip cMuscleAbout
cMuscleBindSticky cMuscleCache cMuscleCompIndex cMuscleQuery cMuscleRayIntersect
cMuscleRelaxSetup cMuscleSimulate cMuscleSplineBind cMuscleWeight cMuscleWeightDefault
cMuscleWeightMirror cMuscleWeightPrune cMuscleWeightSave cacheFile cacheFileCombine
cacheFileMerge cacheFileTrack callbacks camera cameraSet cameraView canCreateManip
canvas ceil changeSubdivComponentDisplayLevel changeSubdivRegion channelBox character
characterMap characterizationToolUICmd characterize chdir checkBox checkBoxGrp
checkDefaultRenderGlobals choice circle circularFillet clamp clear clearCache
clearNClothStartState clearShear clip clipEditor clipEditorCurrentTimeCtx clipMatching
clipSchedule clipSchedulerOutliner closeCurve closeSurface cluster cmdFileOutput
cmdScrollFieldExecuter cmdScrollFieldReporter cmdShell cmdpipe
coarsenSubdivSelectionList collision color colorAtPoint colorEditor colorIndex
colorIndexSliderGrp colorManagementCatalog colorManagementPrefs colorSliderButtonGrp
colorSliderGrp columnLayout commandEcho commandLine commandLogging commandPort
componentBox componentEditor condition cone confirmDialog connectAttr connectControl
connectDynamic connectJoint connectionInfo constrain constrainValue constructionHistory
container containerBind containerProxy containerPublish containerTemplate containerView
contextInfo control convertIffToPsd convertLightmap convertLightmapSetup convertSolidTx
convertTessellation convertUnit copyAttr copyDeformerWeights copyFlexor copyKey copyNode
copySkinWeights cos cosd cosh createAttrPatterns createDisplayLayer createEditor
createLayeredPsdFile createNode createNurbsCircleCtx createNurbsConeCtx
createNurbsCubeCtx createNurbsCylinderCtx createNurbsPlaneCtx createNurbsSphereCtx
createNurbsSquareCtx createNurbsTorusCtx createPolyConeCtx createPolyCubeCtx
createPolyCylinderCtx createPolyHelixCtx createPolyPipeCtx createPolyPlaneCtx
createPolyPlatonicSolidCtx createPolyPrismCtx createPolyPyramidCtx
createPolySoccerBallCtx createPolySphereCtx createPolyTorusCtx createPtexUV
createRenderLayer createSubdivRegion cross ctxAbort ctxCompletion ctxData ctxEditMode
ctxTraverse currentCtx currentTime currentTimeCtx currentUnit curve curveAddPtCtx
curveBezierCtx curveCVCtx curveEPCtx curveEditorCtx curveIntersect curveMoveEPCtx
curveOnSurface curveRGBColor curveSketchCtx customerInvolvementProgram cutKey cycleCheck
cylinder dR_DoCmd dR_activeHandleX dR_activeHandleXY dR_activeHandleXYZ
dR_activeHandleXZ dR_activeHandleY dR_activeHandleYZ dR_activeHandleZ
dR_autoActivateMtkTGL dR_autoWeldTGL dR_bevelPress dR_bevelRelease dR_bevelTool
dR_bridgePress dR_bridgeRelease dR_bridgeTool dR_cameraToPoly dR_connectPress
dR_connectRelease dR_connectTool dR_contextChanged dR_convertSelectionToEdge
dR_convertSelectionToFace dR_convertSelectionToUV dR_convertSelectionToVertex
dR_coordSpaceCustom dR_coordSpaceLocal dR_coordSpaceObject dR_coordSpaceWorld
dR_createCameraFromView dR_curveSnapPress dR_curveSnapRelease dR_customPivotTool
dR_customPivotToolPress dR_customPivotToolRelease dR_cycleCustomCameras
dR_decreaseManipSize dR_defLightTGL dR_disableTexturesTGL dR_edgedFacesTGL
dR_extrudeBevelPress dR_extrudeBevelRelease dR_extrudePress dR_extrudeRelease
dR_extrudeTool dR_graphEditorTGL dR_gridAllTGL dR_gridSnapPress dR_gridSnapRelease
dR_hypergraphTGL dR_hypershadeTGL dR_increaseManipSize dR_loadRecentFile1
dR_loadRecentFile2 dR_loadRecentFile3 dR_loadRecentFile4 dR_lockSelTGL dR_modeEdge
dR_modeMulti dR_modePoly dR_modeUV dR_modeVert dR_movePress dR_moveRelease
dR_moveTweakTool dR_mtkPanelTGL dR_mtkToolTGL dR_multiCutPointCmd dR_multiCutPress
dR_multiCutRelease dR_multiCutSlicePointCmd dR_multiCutTool dR_nexCmd dR_nexTool
dR_objectBackfaceTGL dR_objectEdgesOnlyTGL dR_objectHideTGL dR_objectTemplateTGL
dR_objectXrayTGL dR_outlinerTGL dR_overlayAppendMeshTGL dR_paintPress dR_paintRelease
dR_pointSnapPress dR_pointSnapRelease dR_preferencesTGL dR_quadDrawClearDots
dR_quadDrawPress dR_quadDrawRelease dR_quadDrawTool dR_renderGlobalsTGL dR_renderLastTGL
dR_rotatePress dR_rotateRelease dR_rotateTweakTool dR_safeFrameTGL dR_scalePress
dR_scaleRelease dR_scaleTweakTool dR_selConstraintAngle dR_selConstraintBorder
dR_selConstraintElement dR_selConstraintOff dR_selectAll dR_selectInvert
dR_selectModeHybrid dR_selectModeMarquee dR_selectModeRaycast dR_selectModeTweakMarquee
dR_selectPress dR_selectRelease dR_selectSimilar dR_selectTool dR_setExtendBorder
dR_setExtendEdge dR_setExtendLoop dR_setRelaxAffectsAll dR_setRelaxAffectsAuto
dR_setRelaxAffectsBorders dR_setRelaxAffectsInterior dR_showAbout dR_showHelp
dR_showOptions dR_shrinkWrap dR_slideEdge dR_slideOff dR_slideSurface
dR_softSelDistanceTypeSurface dR_softSelDistanceTypeVolume dR_softSelStickyPress
dR_softSelStickyRelease dR_softSelToolTGL dR_symmetrize dR_symmetryTGL
dR_targetWeldPress dR_targetWeldRelease dR_targetWeldTool dR_testCmd dR_timeConfigTGL
dR_tweakPress dR_tweakRelease dR_vertLockSelected dR_vertSelectLocked dR_vertUnlockAll
dR_viewBack dR_viewBottom dR_viewFront dR_viewGridTGL dR_viewJointsTGL dR_viewLeft
dR_viewLightsTGL dR_viewPersp dR_viewRight dR_viewTop dR_viewXrayTGL dR_visorTGL
dR_wireframeSmoothTGL dagObjectCompare dagObjectHit dagPose dataStructure date dbPeek
dbcount dbmessage dbpeek dbtrace debug debugNamespace debugVar defaultLightListCheckBox
defaultNavigation defineDataServer defineVirtualDevice deformer deformerWeights
deg_to_rad delete deleteAttr deleteAttrPattern deleteExtension deleteGeometryCache
deleteHistoryAheadOfGeomCache deleteNclothCache deleteUI delrandstr detachCurve
detachDeviceAttr detachSurface deviceEditor deviceManager devicePanel dgControl dgInfo
dgPerformance dgcontrol dgdebug dgdirty dgeval dgfilter dgfootprint dgmodified dgstats
dgtimer dimWhen directConnectPath directKeyCtx directionalLight dirmap disable
disableIncorrectNameWarning disconnectAttr disconnectJoint diskCache displacementToPoly
displayAffected displayColor displayCull displayLevelOfDetail displayPref
displayRGBColor displaySmoothness displayStats displayString displaySurface
distanceDimContext distanceDimension dnoise doBlur dockControl dolly dollyCtx
dopeSheetEditor dot doubleProfileBirailSurface dpBirailCtx drag dragAttrContext
draggerContext drawExtrudeFacetCtx dropoffLocator duplicate duplicateCurve
duplicateSurface dynCache dynControl dynExport dynExpression dynGlobals dynPaintCtx
dynPaintEditor dynParticleCtx dynPref dynSelectCtx dynTestData dynWireCtx
dynamicConstraintRemove dynamicLoad editDisplayLayerGlobals editDisplayLayerMembers
editMetadata editRenderLayerAdjustment editRenderLayerGlobals editRenderLayerMembers
editor editorTemplate effector emit emitter enableDevice encodeString env erf erfc error
eval evalContinue evalDeferred evalEcho evalNoSelectNotify event exactWorldBoundingBox
exclusiveLightCheckBox exec exists exp expm1 exportEdits expression
expressionEditorListen extendCurve extendFluid extendSurface extrude fcheck fclose feof
fflush fgetline fgetword file fileBrowserDialog fileDialog fileDialog2 fileInfo
filePathEditor filetest filletCurve filter filterCurve filterExpand findKeyframe
findType fitBspline flagTest flexor floatField floatFieldGrp floatScrollBar floatSlider
floatSlider2 floatSliderButtonGrp floatSliderGrp floor flow flowLayout fluidAppend
fluidAppendOpt fluidCacheInfo fluidDeleteCache fluidDeleteCacheFrames
fluidDeleteCacheFramesOpt fluidDeleteCacheOpt fluidEmitter fluidMergeCache
fluidMergeCacheOpt fluidReplaceCache fluidReplaceCacheOpt fluidReplaceFrames
fluidReplaceFramesOpt fluidVoxelInfo flushIdleQueue flushThumbnailCache flushUndo fmod
fontAttributes fontDialog fopen formLayout format fprint frameBufferName frameLayout
fread freadAllLines freadAllText freeFormFillet frewind fwrite fwriteAllLines
fwriteAllText gameExporter gamma gauss gbGameCommand gbLogManager geoUtils geomBind
geomToBBox geometryAppendCache geometryAppendCacheOpt geometryCache geometryCacheOpt
geometryConstraint geometryDeleteCacheFrames geometryDeleteCacheFramesOpt
geometryDeleteCacheOpt geometryExportCache geometryExportCacheOpt geometryMergeCache
geometryMergeCacheOpt geometryReplaceCache geometryReplaceCacheFrames
geometryReplaceCacheFramesOpt geometryReplaceCacheOpt getAttr getClassification
getDefaultBrush getFileList getFluidAttr getInputDeviceRange getLastError getMetadata
getModifiers getModulePath getPanel getParticleAttr getProcArguments
getRenderDependencies getRenderTasks getenv getpid glRender glRenderEditor globalStitch
gmatch goal gpuCache grabColor gradientControl gradientControlNoAttr graphDollyCtx
graphSelectContext graphTrackCtx gravity greasePencil greasePencilCtx greasePencilHelper
greaseRenderPlane grid gridLayout group groupParts hardenPointCurve hardware
hardwareRenderPanel hasMetadata headsUpDisplay headsUpMessage help helpLine hermite hide
hikBodyPart hikCharacterToolWidget hikCustomRigToolWidget hikGetEffectorIdFromName
hikGetNodeCount hikGetNodeIdFromName hikGlobals hikManip hikRigAlign hikRigSync hilite
hitTest hotBox hotkey hotkeyCheck hsv_to_rgb hudButton hudSlider hudSliderButton
hwReflectionMap hwRender hwRenderLoad hyperGraph hyperPanel hyperShade hypot iGroom
iconTextButton iconTextCheckBox iconTextRadioButton iconTextRadioCollection
iconTextScrollList iconTextStaticLabel igBrush igBrushContext igConvertToLogical
ikHandle ikHandleCtx ikHandleDisplayScale ikSolver ikSplineHandleCtx
ikSpringSolverCallbacks ikSpringSolverRestPose ikSystem ikSystemInfo ikfkDisplayMethod
illustratorCurves image imagePlane imageWindowEditor imfPlugins inViewMessage
inheritTransform insertJoint insertJointCtx insertKeyCtx insertKnotCurve
insertKnotSurface instance instanceable instancer intField intFieldGrp intScrollBar
intSlider intSliderGrp interactionStyle internalVar intersect iprEngine isConnected
isDescendentPulling isDirty isTrue isolateSelect itemFilter itemFilterAttr
itemFilterRender itemFilterType iterOnNurbs joint jointCluster jointCtx
jointDisplayScale jointLattice journal keyTangent keyframe keyframeOutliner
keyframeRegionCurrentTimeCtx keyframeRegionDirectKeyCtx keyframeRegionDollyCtx
keyframeRegionInsertKeyCtx keyframeRegionMoveKeyCtx keyframeRegionScaleKeyCtx
keyframeRegionSelectKeyCtx keyframeRegionSetKeyCtx keyframeRegionTrackCtx keyframeStats
keyingGroup lassoContext lattice latticeDeformKeyCtx launch launchImageEditor
layerButton layeredShaderPort layeredTexturePort layout layoutDialog license
licenseCheck lightList lightlink linearPrecision linstep listAnimatable listAttr
listAttrPatterns listCameras listConnections listDeviceAttachments listHistory
listInputDeviceAxes listInputDeviceButtons listInputDevices listNodeTypes
listNodesWithIncorrectNames listRelatives listSets loadFluid loadModule loadPlugin
loadPrefObjects loadUI lockNode loft log log10 log1p lookThru ls lsThroughFilter lsUI
mag makeIdentity makeLive makePaintable makeSingleSurface makebot manipComponentPivot
manipMoveContext manipMoveLimitsCtx manipOptions manipPivot manipRotateContext
manipRotateLimitsCtx manipScaleContext manipScaleLimitsCtx marker match mateCtx max
maxfloat maxint mayaPreviewRenderIntoNewWindow melInfo memory memoryDiag menu
menuBarLayout menuEditor menuItem menuSet menuSetPref meshIntersectTest messageLine min
minfloat minimizeApp minint mirrorJoint modelCurrentTimeCtx modelEditor modelPanel
modelingToolkitSuperCtx moduleDetectionLogic moduleInfo mouldMesh mouldSrf mouldSubdiv
mouse movIn movOut move moveKeyCtx moveVertexAlongDirection movieCompressor movieInfo
mpBirailCtx mrFactory mrMapVisualizer mrProgress mrShaderManager mtkQuadDrawPoint
mtkShrinkWrap muMessageAdd muMessageDelete muMessageQuery multiProfileBirailSurface
multiTouch mute mw_FloatingMaya mw_vpe myTestCmd nBase nClothAppend nClothAppendOpt
nClothCache nClothCacheOpt nClothCreate nClothCreateOptions nClothDeleteCacheFrames
nClothDeleteCacheFramesOpt nClothDeleteCacheOpt nClothDeleteHistory
nClothDeleteHistoryOpt nClothMakeCollide nClothMakeCollideOptions nClothMergeCache
nClothMergeCacheOpt nClothRemove nClothReplaceCache nClothReplaceCacheOpt
nClothReplaceFrames nClothReplaceFramesOpt nParticle nameCommand nameField namespace
namespaceInfo newton nexConnectContext nexConnectCtx nexCtx nexMultiCutContext
nexMultiCutCtx nexOpt nexQuadDrawContext nexQuadDrawCtx nexTRSContext nodeCast
nodeEditor nodeGrapher nodeIconButton nodeOutliner nodePreset nodeTreeLister nodeType
noise nonLinear nop normalConstraint nucleusDisplayDynamicConstraintNodes
nucleusDisplayMaterialNodes nucleusDisplayNComponentNodes nucleusDisplayOtherNodes
nucleusDisplayTextureNodes nucleusDisplayTransformNodes nucleusGetEffectsAsset
nucleusGetnClothExample nucleusGetnParticleExample nurbsBoolean nurbsCopyUVSet nurbsCube
nurbsCurveRebuildPref nurbsCurveToBezier nurbsEditUV nurbsPlane nurbsSelect nurbsSquare
nurbsToPoly nurbsToPolygonsPref nurbsToSubdiv nurbsToSubdivPref nurbsUVSet objExists
objectCenter objectType objectTypeUI objstats offsetCurve offsetCurveOnSurface
offsetSurface ogs ogsRender ogsdebug openGLExtension openMayaPref optionMenu
optionMenuGrp optionVar orbit orbitCtx orientConstraint outlinerEditor outlinerPanel
overrideModifier paint3d paintEffectsDisplay pairBlend palettePort panZoom panZoomCtx
paneLayout panel panelConfiguration panelHistory paramDimContext paramDimension
paramLocator parent parentConstraint particle particleExists particleFill
particleInstancer particleRenderInfo partition pasteKey pathAnimation pause pclose
perCameraVisibility percent performanceOptions pfxstrokes pickWalk picture pixelMove
planarSrf plane play playbackOptions playblast pluginDisplayFilter pluginInfo
pointConstraint pointCurveConstraint pointLight pointOnCurve pointOnPolyConstraint
pointOnSurface pointPosition poleVectorConstraint polyAppend polyAppendFacetCtx
polyAppendVertex polyAutoProjection polyAverageNormal polyAverageVertex polyBevel
polyBlendColor polyBlindData polyBoolOp polyBridgeEdge polyCBoolOp polyCacheMonitor
polyCheck polyChipOff polyClipboard polyCloseBorder polyCollapseEdge polyCollapseFacet
polyColorBlindData polyColorDel polyColorMod polyColorPerVertex polyColorSet polyCompare
polyCone polyConnectComponents polyCopyUV polyCrease polyCreaseCtx polyCreateFacet
polyCreateFacetCtx polyCube polyCut polyCutCtx polyCylinder polyCylindricalProjection
polyDelEdge polyDelFacet polyDelVertex polyDuplicateAndConnect polyDuplicateEdge
polyEditEdgeFlow polyEditUV polyEditUVShell polyEvaluate polyExtrudeEdge
polyExtrudeFacet polyExtrudeVertex polyFlipEdge polyFlipUV polyForceUV polyGeoSampler
polyHelix polyHole polyInfo polyInstallAction polyIterOnPoly polyLayoutUV
polyListComponentConversion polyMapCut polyMapDel polyMapSew polyMapSewMove
polyMergeEdge polyMergeEdgeCtx polyMergeFacet polyMergeFacetCtx polyMergeUV
polyMergeVertex polyMirrorFace polyMoveEdge polyMoveFacet polyMoveFacetUV polyMoveUV
polyMoveVertex polyMultiLayoutUV polyNormal polyNormalPerVertex polyNormalizeUV
polyOptUvs polyOptions polyOutput polyPipe polyPlanarProjection polyPlane
polyPlatonicSolid polyPoke polyPrimitive polyPrimitiveMisc polyPrism polyProjectCurve
polyProjection polyPyramid polyQuad polyQueryBlindData polyReduce polySelect
polySelectConstraint polySelectConstraintMonitor polySelectCtx polySelectEditCtx
polySelectEditCtxDataCmd polySelectSp polySeparate polySetToFaceNormal polySetVertices
polySewEdge polyShortestPathCtx polySlideEdge polySlideEdgeCtx polySmooth polySoftEdge
polySphere polySphericalProjection polySpinEdge polySplit polySplitCtx polySplitCtx2
polySplitEdge polySplitRing polySplitVertex polyStraightenUVBorder polySubdivideEdge
polySubdivideFacet polySuperCtx polyTestPop polyToCurve polyToSubdiv polyTorus
polyTransfer polyTriangulate polyUVRectangle polyUVSet polyUnite polyUniteSkinned
polyVertexNormalCtx polyWarpImage polyWedgeFace popPinning popen popupMenu pose pow
preloadRefEd prepareRender print profiler profilerTool progressBar progressWindow
projectCurve projectTangent projectionContext projectionManip promptDialog propModCtx
propMove psdChannelOutliner psdConvSolidTxOptions psdEditTextureFile psdExport
psdTextureFile ptexBake pushPinning putenv pwd python querySubdiv quit rad_to_deg radial
radioButton radioButtonGrp radioCollection radioMenuItemCollection rampColorPort
rampWidget rampWidgetAttrless rand randstate rangeControl readPDC readTake rebuildCurve
rebuildSurface recordAttr recordDevice redo reference referenceEdit referenceQuery
refineSubdivSelectionList refresh refreshEditorTemplates regionSelectKeyCtx regmatch
rehash relationship reloadImage removeJoint removeMultiInstance rename renameAttr
renameUI render renderGlobalsNode renderInfo renderLayerPostProcess renderManip
renderPartition renderPassRegistry renderQualityNode renderSettings
renderThumbnailUpdate renderWindowEditor renderWindowSelectContext renderer reorder
reorderContainer reorderDeformers repeatLast requires reroot resampleFluid resetTool
resolutionNode resourceManager retarget retimeHelper retimeKeyCtx reverseCurve
reverseSurface revolve rgb_to_hsv rigidBody rigidSolver roll rollCtx rot rotate
rotationInterpolation roundCRCtx roundConstantRadius rowColumnLayout rowLayout
runTimeCommand runup sampleImage saveAllShelves saveFluid saveImage saveInitialState
saveMenu savePrefObjects savePrefs saveShelf saveToolSettings saveViewportSettings
sbs_AffectTheseAttributes sbs_AffectedByAllInputs sbs_EditSubstance
sbs_GetAllInputsFromSubstanceNode sbs_GetBakeFormat
sbs_GetChannelsNamesFromSubstanceNode sbs_GetEditionModeScale sbs_GetEngine
sbs_GetEnumCount sbs_GetEnumName sbs_GetEnumValue sbs_GetGlobalTextureHeight
sbs_GetGlobalTextureWidth sbs_GetGraphsNamesFromSubstanceNode
sbs_GetPackageFullPathNameFromSubstanceNode sbs_GetSubstanceBuildVersion
sbs_GoToMarketPlace sbs_IsSubstanceRelocalized sbs_SetBakeFormat sbs_SetEditionModeScale
sbs_SetEngine sbs_SetGlobalTextureHeight sbs_SetGlobalTextureWidth scale scaleComponents
scaleConstraint scaleKey scaleKeyCtx sceneEditor sceneUIReplacement scmh scriptCtx
scriptEditorInfo scriptJob scriptNode scriptTable scriptedPanel scriptedPanelType
scrollField scrollLayout sculpt seed selLoadSettings select selectContext selectKey
selectKeyCtx selectKeyframe selectKeyframeRegionCtx selectMode selectPref selectPriority
selectType selectedNodes selectionConnection separator sequenceManager setAttr
setAttrMapping setDefaultShadingGroup setDrivenKeyframe setDynamic setEditCtx
setFluidAttr setFocus setInfinity setInputDeviceMapping setKeyCtx setKeyPath setKeyframe
setKeyframeBlendshapeTargetWts setMenuMode setNClothStartState setNodeTypeFlag setParent
setParticleAttr setRenderPassType setStartupMessage setToolTo setUITemplate
setXformManip sets shaderfx shadingConnection shadingGeometryRelCtx shadingLightRelCtx
shadingNetworkCompare shadingNode shapeCompare shelfButton shelfLayout shelfTabLayout
shot shotRipple shotTrack showHelp showHidden showManipCtx showSelectionInTitle
showShadingGroupAttrEditor showWindow sign simplify sin sind singleProfileBirailSurface
sinh size sizeBytes skinBindCtx skinCluster skinPercent smoothCurve smoothTangentSurface
smoothstep snapKey snapMode snapTogetherCtx snapshot snapshotBeadContext snapshotBeadCtx
snapshotModifyKeyCtx soft softMod softModContext softModCtx softSelect
softSelectOptionsCtx sort sound soundControl spBirailCtx spaceLocator sphere sphrand
spotLight spotLightPreviewPort spreadSheetEditor spring sqrt squareSurface srtContext
stackTrace stitchSurface stitchSurfaceCtx stitchSurfacePoints strcmp
stringArrayIntersector stringArrayRemove stroke subdAutoProjection subdCleanTopology
subdCollapse subdDisplayMode subdDuplicateAndConnect subdEditUV subdLayoutUV
subdListComponentConversion subdMapCut subdMapSewMove subdMatchTopology subdMirror
subdPlanarProjection subdToBlind subdToNurbs subdToPoly subdTransferUVsToCache subdiv
subdivCrease subdivDisplaySmoothness subgraph substitute substituteGeometry substring
suitePrefs superCtx surface surfaceSampler surfaceShaderList swatchDisplayPort
swatchRefresh switchTable symbolButton symbolCheckBox symmetricModelling sysFile system
tabLayout tan tand tangentConstraint tanh targetWeldCtx testPa testPassContribution
texLatticeDeformContext texManipContext texMoveContext texMoveUVShellContext
texRotateContext texScaleContext texSelectContext texSelectShortestPathCtx
texSmoothContext texSmudgeUVContext texTweakUVContext texWinToolCtx text textCurves
textField textFieldButtonGrp textFieldGrp textManip textScrollList textureDeformer
textureLassoContext texturePlacementContext textureWindow threadCount threePointArcCtx
timeCode timeControl timePort timeWarp timer timerX toggle toggleAxis
toggleWindowVisibility tokenize tolerance tolower toolBar toolButton toolCollection
toolDropped toolHasOptions toolPropertyWindow torus toupper trace track trackCtx
transferAttributes transferShadingSets transformCompare transformLimits translator
treeLister treeView trim trimCtx trunc truncateFluidCache truncateHairCache tumble
tumbleCtx turbulence twoPointArcCtx ubercam uiTemplate unassignInputDevice undo undoInfo
unfold ungroup uniform unit unloadPlugin untangleUV untrim upAxis userCtx uvLink
uvSnapshot vectorize vectornum view2dToolCtx viewCamera viewClipPlane viewFit viewHeadOn
viewLookAt viewManip viewPlace viewSet visor volumeAxis volumeBind vortex waitCursor
walkCtx warning webBrowser webBrowserPrefs webView webViewCmd wfnum whatIs
whatsNewHighlight window windowPref wire wireContext workspace wrinkle wrinkleContext
writeTake xform xgmAddGuide xgmBakeGuideVertices xgmBindPatches xgmClumpMap
xgmCopyDescription xgmCurveToGuide xgmDensityComp xgmDraRender xgmExport xgmExportToP3D
xgmFileRender xgmFindAttachment xgmGuideContext xgmGuideGeom xgmGuideRender
xgmInterpSetup xgmMelRender xgmMoveDescription xgmNullRender xgmParticleRender
xgmPatchInfo xgmPointRender xgmPoints xgmPointsContext xgmPolyToGuide xgmPreview
xgmPrimSelectionContext xgmPromoteRender xgmPushOver xgmRebuildCurve xgmSelectedPrims
xgmSetActive xgmSetArchiveSize xgmSetAttr xgmSetGuideCVCount xgmSyncPatchVisibility
xgmWrapXGen xgmr xpmPicker
"""


class MelLexer(QsciLexerCPP):
    # Items in this list will be highlighted using the color for self.GlobalClass
    _highlightedKeywords = ''
    # Mel uses $varName for variables, so we have to allow them in words
    selectionValidator = re.compile('[ \t\n\r\.,?;:!()\[\]+\-\*\/#@^%"\\~&{}|=<>\']')
    wordCharactersOverride = (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$'
    )

    @property
    def highlightedKeywords(self):
        return self._highlightedKeywords

    @highlightedKeywords.setter
    def highlightedKeywords(self, keywords):
        if len(keywords.split(' ')) == 1:
            # If only one keyword was passed in, check if the current selection starts
            # with a $ if so, insert it in front of provided keyword
            parent = self.parent()
            if parent:
                sline, spos, eline, epos = parent.getSelection()
                pos = parent.positionFromLineIndex(sline, spos)
                try:
                    if parent.text()[pos - 1] == '$':
                        keywords = '${}'.format(keywords)
                except IndexError:
                    pass
        self._highlightedKeywords = keywords

    def defaultColor(self, style):
        if style == self.KeywordSet2:
            # Set the highlight color for this lexer
            return QColor(0, 127, 0)
        return super(MelLexer, self).defaultColor(style)

    def defaultFont(self, style):
        if style == self.KeywordSet2:
            return super(MelLexer, self).defaultFont(self.Keyword)
        return super(MelLexer, self).defaultFont(style)

    def defaultPaper(self, style):
        if style == self.GlobalClass:
            # Set the highlight color for this lexer
            return QColor(155, 255, 155)
        return super(MelLexer, self).defaultPaper(style)

    def keywords(self, style):
        if (
            style == 4 and self.highlightedKeywords
        ):  # GlobalClass Used to handle SmartHighlighting
            return self.highlightedKeywords
        elif style == 1:  # Keyword
            return MEL_SYNTAX
        elif style == 2:  # KeywordSet2
            return MEL_KEYWORDS
        return super(MelLexer, self).keywords(style)
