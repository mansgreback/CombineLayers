# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
try:
	from AppKit import NSView, NSButton, NSPopUpButton, NSTextField, NSFont, NSMakeRect
except:
	from Cocoa import NSView, NSButton, NSPopUpButton, NSTextField, NSFont, NSMakeRect

BOOL_OPS = ["Add", "Exclusion", "Intersection"]
PATH_OPS = ["Current", "Revert", "Positive", "Negative"]


class CombineLayers(FilterWithDialog):

	prefID = "com.custom.CombineLayers"

	@objc.python_method
	def settings(self):
		self.menuName = 'Combine Layers'
		self.actionButtonLabel = 'Create Export Instance'
		self.dialog = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 450, 50))

	@objc.python_method
	def start(self):
		try:
			font = Glyphs.font
			if not font:
				return

			for sv in list(self.dialog.subviews()):
				sv.removeFromSuperview()

			masters = list(font.masters)
			masterById = {m.id: m for m in masters}

			extraLayers = set()
			for glyph in font.glyphs:
				for layer in glyph.layers:
					if layer.associatedMasterId != layer.layerId and layer.name:
						extraLayers.add((layer.associatedMasterId, layer.name))

			self.layerRows = []

			width = 450
			cbWidth = 160
			boolWidth = 100
			pathWidth = 90

			currentMasterId = font.selectedFontMaster.id if font.selectedFontMaster else None

			# Collect all rows first
			rows = []
			for m in masters:
				isCurrent = (m.id == currentMasterId)
				rows.append((m.name, None, isCurrent))

			for masterId, layerName in sorted(extraLayers, key=lambda x: (masterById.get(x[0], masters[0]).name, x[1])):
				parentMaster = masterById.get(masterId)
				parentName = parentMaster.name if parentMaster else "?"
				rows.append(("%s / %s" % (parentName, layerName), (layerName, parentName), False))

			# Layout top-down: label at top, then rows in order
			totalHeight = 28 + len(rows) * 26 + 10
			y = totalHeight

			y -= 28
			label2 = NSTextField.alloc().initWithFrame_(NSMakeRect(10, y, width - 20, 17))
			label2.setStringValue_("Layers to combine:")
			label2.setBezeled_(False)
			label2.setDrawsBackground_(False)
			label2.setEditable_(False)
			label2.setSelectable_(False)
			label2.setFont_(NSFont.boldSystemFontOfSize_(11))
			self.dialog.addSubview_(label2)

			for title, extra, isCurrent in rows:
				y -= 26
				cb = NSButton.alloc().initWithFrame_(NSMakeRect(10, y, cbWidth, 22))
				cb.setButtonType_(3)
				cb.setTitle_(title)
				cb.setState_(1 if isCurrent else 0)
				cb.setEnabled_(not isCurrent)
				self.dialog.addSubview_(cb)

				boolOp = NSPopUpButton.alloc().initWithFrame_pullsDown_(
					NSMakeRect(cbWidth + 15, y, boolWidth, 22), False)
				for o in BOOL_OPS:
					boolOp.addItemWithTitle_(o)
				if isCurrent:
					boolOp.setEnabled_(False)
				self.dialog.addSubview_(boolOp)

				pathOp = NSPopUpButton.alloc().initWithFrame_pullsDown_(
					NSMakeRect(cbWidth + boolWidth + 20, y, pathWidth, 22), False)
				for o in PATH_OPS:
					pathOp.addItemWithTitle_(o)
				if isCurrent:
					pathOp.setEnabled_(False)
				self.dialog.addSubview_(pathOp)

				if extra:
					layerName, parentName = extra
				else:
					layerName, parentName = title, None

				self.layerRows.append((cb, boolOp, pathOp, layerName, parentName, isCurrent))

			y = totalHeight

			self.dialog.setFrame_(NSMakeRect(0, 0, width, y))

		except Exception:
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def _createExportInstance(self):
		try:
			selected = self._getSelectedLayers()
			if not selected:
				print("CombineLayers: No layers selected.")
				return

			font = Glyphs.font
			if not font:
				return

			# Find next available CombinedLayers number
			existing = set()
			for inst in font.instances:
				n = inst.name
				if n.startswith("CombinedLayers"):
					try:
						existing.add(int(n[len("CombinedLayers"):]))
					except:
						pass
			num = 1
			while num in existing:
				num += 1
			instName = "CombinedLayers%d" % num

			# Create new instance
			instance = GSInstance()
			instance.name = instName

			# Add Filter custom parameters for each selected layer
			for layerName, masterName, boolOp, pathOp in selected:
				if masterName:
					val = "CombineLayers;%s;%s;%s;%s" % (layerName, boolOp, pathOp, masterName)
				else:
					val = "CombineLayers;%s;%s;%s" % (layerName, boolOp, pathOp)
				instance.customParameters.append(GSCustomParameter("Filter", val))

			font.instances.append(instance)
			print("CombineLayers: Created instance '%s' with %d filter(s)" % (instName, len(selected)))

			# Close the filter dialog
			try:
				window = self.dialog.window()
				if window:
					window.orderOut_(None)
			except:
				pass

			# Open Font Info > Exports tab and select the new instance
			self._newInstanceIndex = list(font.instances).index(instance)
			self._newInstanceFont = font
			self.performSelector_withObject_afterDelay_("openExportsAndSelect", None, 0.1)

		except Exception:
			import traceback
			print(traceback.format_exc())

	def openExportsAndSelect(self):
		try:
			font = getattr(self, '_newInstanceFont', None) or Glyphs.font
			idx = getattr(self, '_newInstanceIndex', None)
			if not font or idx is None:
				return
			wc = font.parent.windowController()

			# Open Font Info directly on the Styles/Exports tab (index 2)
			wc.showFontInfoWindowWithTabSelected_(2)

			# Select the instance after a short delay for the UI to settle
			self.performSelector_withObject_afterDelay_("selectInstance", None, 0.2)
		except Exception:
			import traceback
			print(traceback.format_exc())

	def selectInstance(self):
		try:
			font = getattr(self, '_newInstanceFont', None) or Glyphs.font
			idx = getattr(self, '_newInstanceIndex', None)
			if not font or idx is None:
				return
			wc = font.parent.windowController()
			fic = wc.fontInfoWindowController()
			if not fic:
				return

			# Navigate: fic > contentViewController > tabViewController > childViewControllers[2] (Instances)
			cvc = fic.contentViewController()
			if not cvc:
				return
			tvc = cvc.tabViewController()
			if not tvc:
				return

			# Ensure Styles/Exports tab is selected
			tvc.setSelectedTabViewItemIndex_(2)

			# Get the instance view controller
			children = tvc.childViewControllers()
			if not children or len(children) < 3:
				return
			ivc = children[2]

			# Use instanceArrayController to select the instance
			ac = ivc.instanceArrayController()
			if ac:
				ac.setSelectionIndex_(idx)
		except Exception:
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def generateCustomParameter(self):
		selected = self._getSelectedLayers()
		if not selected:
			return "%s;" % self.__class__.__name__
		layerName, masterName, boolOp, pathOp = selected[0]
		if masterName:
			return "%s;%s;%s;%s;%s" % (self.__class__.__name__, layerName, boolOp, pathOp, masterName)
		else:
			return "%s;%s;%s;%s" % (self.__class__.__name__, layerName, boolOp, pathOp)

	@objc.python_method
	def _findOriginalFont(self):
		try:
			f = Glyphs.font
			if f and len(f.masters) > 1:
				return f
		except:
			pass
		try:
			for f in Glyphs.fonts:
				if f and len(f.masters) > 1:
					return f
		except:
			pass
		return None

	@objc.python_method
	def _findSourceLayer(self, font, glyphName, layerName, parentMasterName=None):
		sourceGlyph = font.glyphs[glyphName]
		if not sourceGlyph:
			return None

		if not parentMasterName:
			for m in font.masters:
				if m.name == layerName:
					return sourceGlyph.layers[m.id]

		parentMasterId = None
		if parentMasterName:
			for m in font.masters:
				if m.name == parentMasterName:
					parentMasterId = m.id
					break

		for l in sourceGlyph.layers:
			if l.name == layerName and l.associatedMasterId != l.layerId:
				if parentMasterId and l.associatedMasterId != parentMasterId:
					continue
				return l
		return None

	@objc.python_method
	def _prepareBShapes(self, addLayer, path_op):
		"""Prepare B shapes based on path direction option."""
		if path_op == "revert":
			shapes = []
			for s in addLayer.shapes:
				c = s.copy()
				c.reverse()
				shapes.append(c)
			return shapes
		elif path_op == "positive":
			temp = addLayer.copy()
			temp.removeOverlap()
			try:
				temp.correctPathDirection()
			except:
				pass
			return [s.copy() for s in temp.shapes]
		elif path_op == "negative":
			temp = addLayer.copy()
			temp.removeOverlap()
			try:
				temp.correctPathDirection()
			except:
				pass
			shapes = []
			for s in temp.shapes:
				c = s.copy()
				c.reverse()
				shapes.append(c)
			return shapes
		else:  # "current"
			return [s.copy() for s in addLayer.shapes]

	@objc.python_method
	def _getResolvedBShapes(self, addLayer):
		"""Resolve B to canonical form (removeOverlap + correctPathDirection).
		Returns all paths including holes, preserving B's actual filled area."""
		temp = addLayer.copy()
		temp.removeOverlap()
		try:
			temp.correctPathDirection()
		except:
			pass
		return [s.copy() for s in temp.shapes]

	@objc.python_method
	def _categorizeBPaths(self, addLayer):
		"""Categorize B paths into positive, inner negative, and freestanding negative."""
		origPaths = [s.copy() for s in addLayer.shapes]
		positive = [s for s in origPaths if s.direction == -1]
		innerNeg = []
		freestandingNeg = []
		for s in origPaths:
			if s.direction != -1:
				sb = s.bounds
				isInner = False
				for p in positive:
					pb = p.bounds
					if (sb.origin.x >= pb.origin.x and
						sb.origin.y >= pb.origin.y and
						sb.origin.x + sb.size.width <= pb.origin.x + pb.size.width and
						sb.origin.y + sb.size.height <= pb.origin.y + pb.size.height):
						isInner = True
						break
				if isInner:
					innerNeg.append(s)
				else:
					freestandingNeg.append(s)
		return positive, innerNeg, freestandingNeg

	@objc.python_method
	def _getBForIntersectExclude(self, addLayer, path_op):
		"""Get B shapes for intersection/exclusion operations."""
		if path_op in ("current", "revert"):
			positive, innerNeg, freestandingNeg = self._categorizeBPaths(addLayer)
			if path_op == "current":
				return positive + innerNeg
			else:
				bShapes = freestandingNeg
				for s in bShapes:
					s.reverse()
				return bShapes
		else:
			return self._getResolvedBShapes(addLayer)

	@objc.python_method
	def _doIntersection(self, layer, bShapes):
		"""A ∩ B using exc7 method."""
		layer.removeOverlap()
		tempAB = layer.copy()
		for s in bShapes:
			c = s.copy(); c.reverse()
			tempAB.shapes.append(c)
		tempAB.removeOverlap()
		tempBA = GSLayer()
		for s in bShapes:
			tempBA.shapes.append(s.copy())
		for s in layer.shapes:
			c = s.copy(); c.reverse()
			tempBA.shapes.append(c)
		tempBA.removeOverlap()
		tempV = layer.copy()
		for s in bShapes:
			tempV.shapes.append(s.copy())
		tempV.removeOverlap()
		for s in tempAB.shapes:
			c = s.copy(); c.reverse()
			tempV.shapes.append(c)
		for s in tempBA.shapes:
			c = s.copy(); c.reverse()
			tempV.shapes.append(c)
		tempV.removeOverlap()
		for s in bShapes:
			layer.shapes.append(s.copy())
		for s in tempV.shapes:
			c = s.copy(); c.reverse()
			layer.shapes.append(c)
		layer.removeOverlap()

	@objc.python_method
	def _doMerge(self, layer, layerName, parentMasterName=None, bool_op="add", path_op="current"):
		glyph = layer.parent
		if not glyph:
			return
		font = self._findOriginalFont()
		if not font:
			return

		addLayer = self._findSourceLayer(font, glyph.name, layerName, parentMasterName)
		if not addLayer:
			return

		if bool_op == "add":
			bShapes = self._prepareBShapes(addLayer, path_op)
			layer.removeOverlap()
			for s in bShapes:
				layer.shapes.append(s)
			layer.removeOverlap()

		elif bool_op == "intersection":
			if path_op == "negative":
				while layer.shapes:
					layer.shapes.pop()
				return
			bInt = self._getBForIntersectExclude(addLayer, path_op)
			if not bInt:
				return
			self._doIntersection(layer, bInt)

		elif bool_op == "exclusion":
			# Exclusion = A minus B (only remove, never add)
			# Computed as A - (A∩B) to guarantee nothing outside A is created
			if path_op == "negative":
				layer.removeOverlap()
				return
			bExc = self._getBForIntersectExclude(addLayer, path_op)
			if not bExc:
				layer.removeOverlap()
				return
			# Compute A∩B using exc7 on a copy
			layer.removeOverlap()
			intLayer = layer.copy()
			tempAB = intLayer.copy()
			for s in bExc:
				c = s.copy(); c.reverse()
				tempAB.shapes.append(c)
			tempAB.removeOverlap()
			tempBA = GSLayer()
			for s in bExc:
				tempBA.shapes.append(s.copy())
			for s in intLayer.shapes:
				c = s.copy(); c.reverse()
				tempBA.shapes.append(c)
			tempBA.removeOverlap()
			tempV = intLayer.copy()
			for s in bExc:
				tempV.shapes.append(s.copy())
			tempV.removeOverlap()
			for s in tempAB.shapes:
				c = s.copy(); c.reverse()
				tempV.shapes.append(c)
			for s in tempBA.shapes:
				c = s.copy(); c.reverse()
				tempV.shapes.append(c)
			tempV.removeOverlap()
			tempInt = intLayer.copy()
			for s in bExc:
				tempInt.shapes.append(s.copy())
			for s in tempV.shapes:
				c = s.copy(); c.reverse()
				tempInt.shapes.append(c)
			tempInt.removeOverlap()
			# Subtract A∩B from A (safe: A∩B is entirely within A)
			for s in tempInt.shapes:
				c = s.copy(); c.reverse()
				layer.shapes.append(c)
			layer.removeOverlap()

	@objc.python_method
	def _getSelectedLayers(self):
		if not hasattr(self, 'layerRows'):
			return []
		result = []
		for cb, boolDropdown, pathDropdown, name, masterName, isBase in self.layerRows:
			if isBase:
				continue
			if cb.state() == 1:
				boolOp = str(boolDropdown.titleOfSelectedItem()).lower()
				pathOp = str(pathDropdown.titleOfSelectedItem()).lower()
				result.append((name, masterName, boolOp, pathOp))
		return result

	def process_(self, sender):
		"""Override action button to create export instance instead of applying filter."""
		self._createExportInstance()

	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		try:
			if not customParameters:
				return

			layerName = customParameters.get(0)
			if not layerName:
				return

			param1 = str(customParameters.get(1, "add")).lower()
			param2 = customParameters.get(2)
			param3 = customParameters.get(3)

			validBoolOps = ("add", "exclusion", "intersection")
			validPathOps = ("current", "revert", "positive", "negative")

			# Legacy names (from old MergeLayer plugin and Glyphs-reserved keywords)
			legacyMap = {
				"combine": ("add", "current"),
				"reverse": ("add", "revert"),
				"intersect": ("intersection", "current"),
				"include": ("intersection", "current"),
				"exclude": ("exclusion", "current"),
			}

			if param1 in legacyMap:
				bool_op, path_op = legacyMap[param1]
				parentMasterName = str(param2) if param2 else None
			elif param1 in validBoolOps:
				bool_op = param1
				if param2 and str(param2).lower() in validPathOps:
					path_op = str(param2).lower()
					parentMasterName = str(param3) if param3 else None
				else:
					path_op = "current"
					parentMasterName = str(param2) if param2 else None
			else:
				# param1 is parentMasterName (legacy format)
				parentMasterName = param1
				bool_op = "add"
				path_op = "current"
				if param2:
					p2 = str(param2).lower()
					if p2 in legacyMap:
						bool_op, path_op = legacyMap[p2]
					elif p2 in validBoolOps:
						bool_op = p2
						if param3 and str(param3).lower() in validPathOps:
							path_op = str(param3).lower()

			self._doMerge(layer, layerName, parentMasterName, bool_op, path_op)
		except Exception:
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def __file__(self):
		return __file__
