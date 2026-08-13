import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Download,
  Edit3,
  FileJson,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  Layers3,
  LoaderCircle,
  Maximize2,
  Menu,
  MessageSquareText,
  Minus,
  MousePointer2,
  Plus,
  Redo2,
  Search,
  SkipForward,
  Undo2,
  Upload,
  X,
} from "lucide-react";

const REVIEW_FILTERS = ["all", "unresolved", "changed"];
const SUGGESTIONS = ["400", "450", "Varies"];
const POLYGON_PROFILE_SHAPES = new Set([
  "tee",
  "inverted_tee",
  "l_shape",
  "custom",
]);
const PROFILE_SHAPES = [
  "tapered",
  "haunched",
  "tee",
  "inverted_tee",
  "l_shape",
  "custom",
];

function profileLabel(shape) {
  const label = shape?.replaceAll("_", " ");
  return label ? `${label[0].toUpperCase()}${label.slice(1)}` : "Complex profile";
}

function profileSummary(profile) {
  if (!profile) return null;
  const stationCount = profile.stations?.length || 0;
  return `${profileLabel(profile.shape)} · ${stationCount} ${
    stationCount === 1 ? "station" : "stations"
  }`;
}

function formatDimension(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(
    value,
  );
}

function cloneProfile(profile) {
  return profile ? structuredClone(profile) : null;
}

function validateProfile(profile, beamLength) {
  if (!profile) return "";
  if (!PROFILE_SHAPES.includes(profile.shape)) return "Choose a profile shape.";
  if (!profile.start_location?.trim())
    return "Name the grid or support used as station zero.";
  if (!profile.stations?.length) return "Add at least one profile station.";

  let previousDistance = -1;
  for (const [index, station] of profile.stations.entries()) {
    const distance = Number(station.distance);
    if (!Number.isFinite(distance) || distance < 0)
      return `Station ${index + 1} needs a non-negative distance.`;
    if (distance <= previousDistance)
      return "Station distances must be strictly increasing.";
    if (Number.isFinite(beamLength) && distance > beamLength)
      return `Station ${index + 1} lies beyond the beam length.`;
    previousDistance = distance;

    if (POLYGON_PROFILE_SHAPES.has(profile.shape)) {
      if (!station.vertices || station.vertices.length < 3)
        return `Station ${index + 1} needs at least three vertices.`;
      if (
        station.vertices.some(
          (point) =>
            !Number.isFinite(Number(point.x)) ||
            !Number.isFinite(Number(point.y)) ||
            Number(point.x) < 0 ||
            Number(point.y) < 0,
        )
      )
        return `Station ${index + 1} needs non-negative x and y coordinates.`;
      const area = Math.abs(
        station.vertices.reduce((sum, point, pointIndex, points) => {
          const next = points[(pointIndex + 1) % points.length];
          return (
            sum +
            Number(point.x) * Number(next.y) -
            Number(next.x) * Number(point.y)
          );
        }, 0) / 2,
      );
      if (area === 0)
        return `Station ${index + 1} vertices must enclose a cross-section area.`;
    } else if (
      !Number.isFinite(Number(station.width)) ||
      Number(station.width) <= 0 ||
      !Number.isFinite(Number(station.depth)) ||
      Number(station.depth) <= 0
    ) {
      return `Station ${index + 1} needs positive width and depth values.`;
    }
  }
  return "";
}

function memberDimensionKeys(member) {
  if (member.kind === "column") return ["width", "depth", "height", "unit"];
  return member.profile
    ? ["length", "unit"]
    : ["width", "depth", "length", "unit"];
}

function memberStatus(member) {
  if (member.reviewStatus) return member.reviewStatus;
  return memberDimensionKeys(member).some((field) => member[field] == null)
    ? "unresolved"
    : "confirmed";
}

function normalizeData(data, positionData) {
  const positions = new Map(
    [...positionData.beams, ...positionData.columns].map((record) => [
      record.key,
      record,
    ]),
  );
  const withPosition = (member, kind) => {
    const record = positions.get(member.key);
    const memberPositions = record?.positions?.length
      ? record.positions
      : record?.position
        ? [record.position]
        : [];
    return {
      ...member,
      position: record?.position ?? null,
      positions: record?.positions ?? null,
      positionBoxes: memberPositions,
      position_null_reason:
        record?.position_null_reason ??
        "No third-pass position record was loaded.",
      kind,
      original: { ...member },
    };
  };
  return [
    ...data.beams.map((member) => withPosition(member, "beam")),
    ...data.columns.map((member) => withPosition(member, "column")),
  ];
}

async function fetchReviewData() {
  const [memberResponse, positionResponse] = await Promise.all([
    fetch("/second_pass_result.json"),
    fetch("/third_pass_result.json"),
  ]);
  if (!memberResponse.ok)
    throw new Error("The second-pass member file could not be loaded.");
  if (!positionResponse.ok)
    throw new Error("The third-pass position file could not be loaded.");
  return normalizeData(
    await memberResponse.json(),
    await positionResponse.json(),
  );
}

function getMissingField(member) {
  return (
    memberDimensionKeys(member).find((field) => member[field] == null) || null
  );
}

function downloadBlob(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [screen, setScreen] = useState("upload");
  const [file, setFile] = useState(null);
  const [members, setMembers] = useState([]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [kind, setKind] = useState("beam");
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [analysisStep, setAnalysisStep] = useState(0);
  const [analysisError, setAnalysisError] = useState("");
  const [history, setHistory] = useState([]);
  const [future, setFuture] = useState([]);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});
  const [editError, setEditError] = useState("");
  const [note, setNote] = useState("");
  const [exportOpen, setExportOpen] = useState(false);
  const [exportWarning, setExportWarning] = useState(null);
  const [pdfZoom, setPdfZoom] = useState(100);
  const [viewPage, setViewPage] = useState(1);
  const [toast, setToast] = useState("");
  const fileInput = useRef(null);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("demo") !== "workspace")
      return;
    setFile({ name: "plan.pdf", size: 3431424, sample: true });
    fetchReviewData()
      .then((data) => {
        const firstUnresolved =
          data.find((member) => memberStatus(member) === "unresolved") ||
          data[0];
        setMembers(data);
        setKind(firstUnresolved.kind);
        setSelectedKey(firstUnresolved.key);
        setScreen("workspace");
      })
      .catch((error) => {
        setAnalysisError(error.message);
        setScreen("analysis-error");
      });
  }, []);

  const selected = members.find((member) => member.key === selectedKey) || null;
  const citedPages = useMemo(() => {
    if (!selected) return [];
    const missing = getMissingField(selected);
    const reason = missing ? selected[`${missing}_null_reason`] || "" : "";
    return [
      ...new Set(
        [...reason.matchAll(/page\s+(\d+)/gi)].map((match) => Number(match[1])),
      ),
    ];
  }, [selected]);
  const counts = useMemo(
    () => ({
      beam: members.filter((member) => member.kind === "beam").length,
      column: members.filter((member) => member.kind === "column").length,
      unresolved: members.filter(
        (member) => memberStatus(member) === "unresolved",
      ).length,
      changed: members.filter((member) => memberStatus(member) === "changed")
        .length,
      reviewed: members.filter((member) =>
        ["confirmed", "changed"].includes(memberStatus(member)),
      ).length,
    }),
    [members],
  );

  const visibleMembers = useMemo(
    () =>
      members.filter((member) => {
        if (member.kind !== kind) return false;
        if (filter !== "all" && memberStatus(member) !== filter) return false;
        const query = search.trim().toLowerCase();
        return (
          !query ||
          `${member.drawing_id || ""} ${member.location} ${member.level || ""}`
            .toLowerCase()
            .includes(query)
        );
      }),
    [members, kind, filter, search],
  );
  const pageMembers = useMemo(
    () =>
      members
        .filter(
          (member) => member.page === viewPage && member.positionBoxes.length,
        )
        .sort(
          (a, b) =>
            Number(a.key === selectedKey) - Number(b.key === selectedKey),
        ),
    [members, selectedKey, viewPage],
  );

  const nextUnresolved = () => {
    const currentIndex = members.findIndex(
      (member) => member.key === selectedKey,
    );
    const ordered = [
      ...members.slice(currentIndex + 1),
      ...members.slice(0, currentIndex + 1),
    ];
    const next = ordered.find(
      (member) => memberStatus(member) === "unresolved",
    );
    if (next) {
      setKind(next.kind);
      setFilter("all");
      setSelectedKey(next.key);
    } else setToast("Every member has been reviewed.");
  };

  useEffect(() => {
    if (selected?.page) setViewPage(selected.page);
  }, [selectedKey]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(""), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    const handleKey = (event) => {
      if (
        screen !== "workspace" ||
        event.target.matches("input, textarea, select")
      )
        return;
      if (event.key.toLowerCase() === "n") nextUnresolved();
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
        event.preventDefault();
        undo();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  const loadExtraction = async () => {
    const data = await fetchReviewData();
    setMembers(data);
    const firstUnresolved =
      data.find((member) => memberStatus(member) === "unresolved") || data[0];
    setKind(firstUnresolved.kind);
    setSelectedKey(firstUnresolved.key);
  };

  const analyze = async () => {
    if (!file) return;
    setAnalysisError("");
    setAnalysisStep(0);
    setScreen("analyzing");
    try {
      for (let step = 1; step <= 4; step += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 520));
        setAnalysisStep(step);
      }
      await loadExtraction();
      setScreen("workspace");
    } catch (error) {
      setAnalysisError(error.message);
      setScreen("analysis-error");
    }
  };

  const openSample = () => {
    setFile({ name: "plan.pdf", size: 3431424, sample: true });
  };

  const snapshotAndUpdate = (nextMember, message) => {
    setHistory((items) => [...items, { members, selectedKey, message }]);
    setFuture([]);
    setMembers((items) =>
      items.map((member) =>
        member.key === nextMember.key ? nextMember : member,
      ),
    );
    setToast(message);
  };

  const resolveField = (value) => {
    const field = getMissingField(selected);
    if (!field) return;
    const nextValue = value === "Varies" ? value : Number(value);
    const next = {
      ...selected,
      [field]: nextValue,
      [`${field}_null_reason`]: null,
      reviewStatus: "changed",
      reviewNote: `Resolved from review: ${value}${value === "Varies" ? "" : ` ${selected.unit || "mm"}`}`,
    };
    snapshotAndUpdate(next, `${selected.drawing_id || "Member"} updated.`);
    nextUnresolved();
  };

  const markUnresolved = (status) => {
    const next = {
      ...selected,
      reviewStatus: status,
      reviewNote:
        status === "skipped"
          ? "Skipped for later review."
          : "Reviewer could not determine an exact value.",
    };
    snapshotAndUpdate(
      next,
      status === "skipped" ? "Member skipped." : "Marked cannot determine.",
    );
    nextUnresolved();
  };

  const beginEdit = () => {
    setDraft({
      width: selected.width ?? "",
      depth: selected.depth ?? "",
      length: selected.length ?? "",
      height: selected.height ?? "",
      level: selected.level ?? "",
      location: selected.location,
      profile: cloneProfile(selected.profile),
      profile_null_reason: selected.profile_null_reason ?? "",
    });
    setNote(selected.reviewNote || "");
    setEditError("");
    setEditing(true);
  };

  const saveEdit = () => {
    const numeric = (value) => (value === "" ? null : Number(value));
    const length = selected.kind === "beam" ? numeric(draft.length) : null;
    const profileError = validateProfile(draft.profile, length);
    if (profileError) {
      setEditError(profileError);
      return;
    }
    const profile = cloneProfile(draft.profile);
    const width = profile ? null : numeric(draft.width);
    const depth = profile ? null : numeric(draft.depth);
    if (profile) {
      profile.start_location = profile.start_location.trim();
      profile.stations = profile.stations.map((station) => ({
        distance: Number(station.distance),
        width: POLYGON_PROFILE_SHAPES.has(profile.shape)
          ? null
          : Number(station.width),
        depth: POLYGON_PROFILE_SHAPES.has(profile.shape)
          ? null
          : Number(station.depth),
        vertices: POLYGON_PROFILE_SHAPES.has(profile.shape)
          ? station.vertices.map((point) => ({
              x: Number(point.x),
              y: Number(point.y),
            }))
          : null,
      }));
    }
    const next = {
      ...selected,
      width,
      width_null_reason: profile
        ? "The cross-section is represented by exact profile stations."
        : width == null
          ? selected.width_null_reason || "Not established in manual review."
          : null,
      depth,
      depth_null_reason: profile
        ? "The cross-section is represented by exact profile stations."
        : depth == null
          ? selected.depth_null_reason || "Not established in manual review."
          : null,
      ...(selected.kind === "beam"
        ? {
            length,
            length_null_reason:
              length == null
                ? selected.length_null_reason ||
                  "Not established in manual review."
                : null,
            profile,
            profile_null_reason: profile
              ? null
              : draft.profile_null_reason.trim() ||
                "Legacy extraction has no profile assessment; verify the applicable section or detail.",
          }
        : {
            height: numeric(draft.height),
            height_null_reason:
              numeric(draft.height) == null
                ? selected.height_null_reason ||
                  "Not established in manual review."
                : null,
          }),
      level: draft.level || null,
      location: draft.location.trim() || selected.location,
      reviewStatus: "changed",
      reviewNote: note.trim(),
    };
    snapshotAndUpdate(
      next,
      `${selected.drawing_id || "Member"} changes saved.`,
    );
    setEditError("");
    setEditing(false);
  };

  const undo = () => {
    const last = history.at(-1);
    if (!last) return;
    setFuture((items) => [{ members, selectedKey }, ...items]);
    setMembers(last.members);
    setSelectedKey(last.selectedKey);
    setHistory((items) => items.slice(0, -1));
    setToast("Last change undone.");
  };

  const redo = () => {
    const next = future[0];
    if (!next) return;
    setHistory((items) => [...items, { members, selectedKey }]);
    setMembers(next.members);
    setSelectedKey(next.selectedKey);
    setFuture((items) => items.slice(1));
    setToast("Change restored.");
  };

  const exportData = (format, acknowledged = false) => {
    const unresolvedCount = members.filter((member) =>
      ["unresolved", "skipped", "cannot-determine"].includes(
        memberStatus(member),
      ),
    ).length;
    if (unresolvedCount && !acknowledged) {
      setExportWarning({ format, unresolvedCount });
      setExportOpen(false);
      return;
    }
    const clean = (member) => {
      const { original, positionBoxes, ...rest } = member;
      return rest;
    };
    if (format === "json") {
      downloadBlob(
        JSON.stringify(
          {
            beams: members.filter((m) => m.kind === "beam").map(clean),
            columns: members.filter((m) => m.kind === "column").map(clean),
          },
          null,
          2,
        ),
        "reviewed-members.json",
        "application/json",
      );
    } else {
      const headers = [
        "type",
        "drawing_id",
        "page",
        "level",
        "location",
        "width",
        "depth",
        "length_or_height",
        "unit",
        "profile_shape",
        "profile_stations",
        "review_status",
        "review_note",
      ];
      const rows = members.map((member) => [
        member.kind,
        member.drawing_id,
        member.page,
        member.level,
        member.location,
        member.width,
        member.depth,
        member.kind === "beam" ? member.length : member.height,
        member.unit,
        member.profile?.shape || "",
        member.profile ? JSON.stringify(member.profile.stations) : "",
        memberStatus(member),
        member.reviewNote || "",
      ]);
      const csv = [headers, ...rows]
        .map((row) =>
          row
            .map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`)
            .join(","),
        )
        .join("\n");
      downloadBlob(csv, "reviewed-members.csv", "text/csv");
    }
    setExportWarning(null);
    setToast(`${format.toUpperCase()} export prepared.`);
  };

  if (screen === "upload")
    return (
      <UploadScreen
        file={file}
        setFile={setFile}
        fileInput={fileInput}
        openSample={openSample}
        analyze={analyze}
      />
    );
  if (screen === "analyzing")
    return (
      <AnalysisScreen
        file={file}
        step={analysisStep}
        onCancel={() => setScreen("upload")}
      />
    );
  if (screen === "analysis-error")
    return (
      <ErrorScreen
        message={analysisError}
        retry={analyze}
        back={() => setScreen("upload")}
      />
    );

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="icon-button mobile-menu" aria-label="Open menu">
          <Menu size={19} />
        </button>
        <div className="file-identity">
          <span className="app-mark">
            <Layers3 size={18} />
          </span>
          <div>
            <strong>{file?.name || "plan.pdf"}</strong>
            <span>Structural Drawing Assistant</span>
          </div>
        </div>
        <div
          className="review-progress"
          aria-label={`${counts.reviewed} of ${members.length} reviewed`}
        >
          <span>Review progress</span>
          <progress value={counts.reviewed} max={members.length} />
          <strong>
            {counts.reviewed} of {members.length}
          </strong>
        </div>
        <div className="top-actions">
          <button
            className="button secondary compact"
            onClick={undo}
            disabled={!history.length}
          >
            <Undo2 size={16} />
            Undo
          </button>
          <button
            className="icon-button"
            aria-label="Redo"
            onClick={redo}
            disabled={!future.length}
          >
            <Redo2 size={16} />
          </button>
          <div className="export-wrap">
            <button
              className="button primary"
              onClick={() => setExportOpen((open) => !open)}
            >
              <Download size={17} />
              Export
              <ChevronDown size={15} />
            </button>
            {exportOpen && (
              <div className="export-menu">
                <button onClick={() => exportData("json")}>
                  <FileJson size={18} />
                  <span>
                    <strong>Reviewed JSON</strong>
                    <small>Preserves null reasons and review notes</small>
                  </span>
                </button>
                <button onClick={() => exportData("csv")}>
                  <FileSpreadsheet size={18} />
                  <span>
                    <strong>Reviewed CSV</strong>
                    <small>Flat table for estimating workflows</small>
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="workspace">
        <MemberNavigator
          members={visibleMembers}
          counts={counts}
          kind={kind}
          setKind={setKind}
          filter={filter}
          setFilter={setFilter}
          search={search}
          setSearch={setSearch}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
        />
        <section className="evidence-workspace">
          <div className="viewer-toolbar">
            <div className="tool-group">
              <button className="icon-button selected" aria-label="Select">
                <MousePointer2 size={17} />
              </button>
              <button
                className="icon-button"
                aria-label="Fit page"
                onClick={() => setPdfZoom(100)}
              >
                <Maximize2 size={17} />
              </button>
              <div
                className="overlay-legend"
                aria-label="Member overlay legend"
              >
                <span>
                  <i className="beam-swatch">B</i>Beam
                </span>
                <span>
                  <i className="column-swatch">C</i>Column
                </span>
              </div>
            </div>
            <div className="page-label">
              <FileText size={16} />
              <button
                className="icon-button"
                aria-label="Previous page"
                onClick={() => setViewPage((page) => Math.max(1, page - 1))}
                disabled={viewPage === 1}
              >
                <ChevronLeft size={15} />
              </button>
              <label>
                Page{" "}
                <input
                  aria-label="Drawing page"
                  type="number"
                  min="1"
                  max="15"
                  value={viewPage}
                  onChange={(event) =>
                    setViewPage(
                      Math.min(
                        15,
                        Math.max(1, Number(event.target.value) || 1),
                      ),
                    )
                  }
                />
              </label>
              <span>of 15</span>
              <button
                className="icon-button"
                aria-label="Next page"
                onClick={() => setViewPage((page) => Math.min(15, page + 1))}
                disabled={viewPage === 15}
              >
                <ChevronRight size={15} />
              </button>
            </div>
            <div className="tool-group zoom-tools">
              <button
                className="icon-button"
                aria-label="Zoom out"
                onClick={() => setPdfZoom((zoom) => Math.max(50, zoom - 10))}
              >
                <Minus size={17} />
              </button>
              <span>{pdfZoom}%</span>
              <button
                className="icon-button"
                aria-label="Zoom in"
                onClick={() => setPdfZoom((zoom) => Math.min(180, zoom + 10))}
              >
                <Plus size={17} />
              </button>
            </div>
          </div>
          <div className="pdf-stage">
            <div className="drawing-scroll">
              <div className="drawing-sheet" style={{ width: `${pdfZoom}%` }}>
                <img
                  alt={`Rendered source drawing page ${viewPage}`}
                  src={`/drawing-pages/page-${viewPage}.webp`}
                />
                <div
                  className="member-overlay"
                  aria-label={`Structural members on page ${viewPage}`}
                >
                  {pageMembers.flatMap((member) =>
                    member.positionBoxes.map((position, segmentIndex) => (
                      <MemberPosition
                        key={`${member.key}-${segmentIndex}`}
                        member={member}
                        position={position}
                        segmentIndex={segmentIndex}
                        segmentCount={member.positionBoxes.length}
                        selected={member.key === selectedKey}
                        onSelect={() => {
                          setKind(member.kind);
                          setFilter("all");
                          setSelectedKey(member.key);
                        }}
                      />
                    )),
                  )}
                </div>
              </div>
            </div>
            <div className="evidence-notice">
              <CircleHelp size={15} />
              <span>
                {pageMembers.length
                  ? `${pageMembers.length} member ${pageMembers.length === 1 ? "location" : "locations"} on page ${viewPage}. Select an outline to review it.`
                  : `No positioned members on page ${viewPage}.`}
              </span>
              {viewPage !== selected?.page && (
                <button onClick={() => setViewPage(selected.page)}>
                  Occurrence page {selected.page}
                </button>
              )}
              {citedPages
                .filter((page) => page !== viewPage)
                .map((page) => (
                  <button key={page} onClick={() => setViewPage(page)}>
                    Cited page {page}
                  </button>
                ))}
            </div>
          </div>
          {selected && (
            <ReviewTray
              member={selected}
              editing={editing}
              setEditing={setEditing}
              beginEdit={beginEdit}
              draft={draft}
              setDraft={setDraft}
              note={note}
              setNote={setNote}
              editError={editError}
              saveEdit={saveEdit}
              resolveField={resolveField}
              markUnresolved={markUnresolved}
              nextUnresolved={nextUnresolved}
              citedPages={citedPages}
              setViewPage={setViewPage}
            />
          )}
        </section>
      </div>
      {exportWarning && (
        <ExportWarning
          warning={exportWarning}
          cancel={() => setExportWarning(null)}
          proceed={() => exportData(exportWarning.format, true)}
        />
      )}
      {toast && (
        <div className="toast" role="status">
          <Check size={17} />
          {toast}
        </div>
      )}
    </main>
  );
}

function MemberPosition({
  member,
  position,
  segmentIndex,
  segmentCount,
  selected,
  onSelect,
}) {
  const { left, top, right, bottom } = position;
  const label = `${member.kind === "beam" ? "Beam" : "Column"} ${member.drawing_id || "unlabelled"}: ${member.location}`;
  const segmentLabel =
    segmentCount > 1
      ? `, segment ${segmentIndex + 1} of ${segmentCount}`
      : "";
  return (
    <button
      type="button"
      className={`member-position ${member.kind} ${selected ? "selected" : ""}`}
      style={{
        left: `${left * 100}%`,
        top: `${top * 100}%`,
        width: `${(right - left) * 100}%`,
        height: `${(bottom - top) * 100}%`,
      }}
      aria-label={`Select ${label}${segmentLabel}`}
      title={label}
      onClick={onSelect}
    >
      {segmentIndex === 0 && (
        <span aria-hidden="true">
          {member.kind === "beam" ? "B" : "C"} · {member.drawing_id || "—"}
        </span>
      )}
    </button>
  );
}

function UploadScreen({ file, setFile, fileInput, openSample, analyze }) {
  const acceptFile = (candidate) => {
    if (
      candidate?.type === "application/pdf" ||
      candidate?.name?.toLowerCase().endsWith(".pdf")
    )
      setFile(candidate);
  };
  return (
    <main className="setup-screen">
      <header className="setup-header">
        <span className="app-mark">
          <Layers3 size={19} />
        </span>
        <strong>Structural Drawing Assistant</strong>
        <span className="prototype-tag">Review workspace</span>
      </header>
      <section className="setup-content">
        <div className="setup-copy">
          <h1>Review structural members against the drawing.</h1>
          <p>
            Select a complete construction drawing set. The workspace keeps
            extracted dimensions, unresolved values, and source pages together.
          </p>
        </div>
        <div
          className={`drop-zone ${file ? "has-file" : ""}`}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            acceptFile(event.dataTransfer.files[0]);
          }}
        >
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(event) => acceptFile(event.target.files[0])}
          />
          {file ? (
            <>
              <span className="file-icon">
                <FileText size={28} />
              </span>
              <div>
                <strong>{file.name}</strong>
                <span>
                  {(file.size / 1024 / 1024).toFixed(1)} MB · PDF drawing set
                </span>
              </div>
              <button
                className="button secondary"
                onClick={() => fileInput.current?.click()}
              >
                Replace
              </button>
            </>
          ) : (
            <>
              <span className="upload-icon">
                <Upload size={24} />
              </span>
              <h2>Drop a drawing PDF here</h2>
              <p>
                Use the complete set so plans, schedules, sections, and details
                stay together.
              </p>
              <button
                className="button secondary"
                onClick={() => fileInput.current?.click()}
              >
                <FolderOpen size={17} />
                Choose PDF
              </button>
            </>
          )}
        </div>
        <div className="setup-actions">
          <button className="text-button" onClick={openSample}>
            Use bundled plan.pdf
          </button>
          <button
            className="button primary large"
            disabled={!file}
            onClick={analyze}
          >
            Analyze drawing
            <ChevronRight size={18} />
          </button>
        </div>
        <p className="demo-note">
          <AlertCircle size={15} />
          This prototype joins members from <code>
            second_pass_result.json
          </code>{" "}
          with positions from <code>third_pass_result.json</code>.
        </p>
      </section>
    </main>
  );
}

function AnalysisScreen({ file, step, onCancel }) {
  const steps = [
    "Opening drawing set",
    "Reading extracted members",
    "Checking unresolved dimensions",
    "Preparing review workspace",
  ];
  return (
    <main className="analysis-screen">
      <div className="analysis-panel">
        <span className="analysis-icon">
          <LoaderCircle size={28} />
        </span>
        <h1>Preparing {file?.name}</h1>
        <p>
          Keeping the drawing and second-pass member inventory together for
          review.
        </p>
        <div className="analysis-steps">
          {steps.map((label, index) => (
            <div
              className={
                index < step ? "complete" : index === step ? "active" : ""
              }
              key={label}
            >
              <span>{index < step ? <Check size={14} /> : index + 1}</span>
              <strong>{label}</strong>
            </div>
          ))}
        </div>
        <button className="button secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </main>
  );
}

function ErrorScreen({ message, retry, back }) {
  return (
    <main className="analysis-screen">
      <div className="analysis-panel error-panel">
        <span className="error-icon">
          <AlertCircle size={28} />
        </span>
        <h1>Analysis could not be prepared</h1>
        <p>{message}</p>
        <div className="inline-actions">
          <button className="button secondary" onClick={back}>
            <ArrowLeft size={16} />
            Choose another PDF
          </button>
          <button className="button primary" onClick={retry}>
            Try again
          </button>
        </div>
      </div>
    </main>
  );
}

function MemberNavigator({
  members,
  counts,
  kind,
  setKind,
  filter,
  setFilter,
  search,
  setSearch,
  selectedKey,
  setSelectedKey,
}) {
  return (
    <aside className="member-nav">
      <div className="nav-heading">
        <h2>Members</h2>
        <span className="nav-count">{counts[kind]} total</span>
      </div>
      <label className="search-field">
        <Search size={16} />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search ID or location"
        />
      </label>
      <div className="tabs" role="tablist">
        <button
          className={kind === "beam" ? "active" : ""}
          onClick={() => setKind("beam")}
        >
          Beams <span>{counts.beam}</span>
        </button>
        <button
          className={kind === "column" ? "active" : ""}
          onClick={() => setKind("column")}
        >
          Columns <span>{counts.column}</span>
        </button>
      </div>
      <div className="filter-row">
        {REVIEW_FILTERS.map((name) => (
          <button
            key={name}
            className={filter === name ? "active" : ""}
            onClick={() => setFilter(name)}
          >
            {name === "all" ? "All" : name}
            <span>{name === "all" ? counts[kind] : counts[name]}</span>
          </button>
        ))}
      </div>
      <div className="member-list" role="listbox" aria-label={`${kind}s`}>
        {members.length ? (
          members.map((member) => {
            const status = memberStatus(member);
            return (
              <button
                role="option"
                aria-selected={member.key === selectedKey}
                className={`member-row ${member.key === selectedKey ? "selected" : ""}`}
                key={member.key}
                onClick={() => setSelectedKey(member.key)}
              >
                <span className={`status-dot ${status}`} aria-hidden="true" />
                <span className="member-copy">
                  <strong>{member.drawing_id || "Unlabelled"}</strong>
                  <small>
                    {member.location}
                    {member.profile
                      ? ` · ${profileLabel(member.profile.shape)}`
                      : ""}
                  </small>
                </span>
                <span className={`status-icon ${status}`}>
                  {status === "confirmed" ? (
                    <Check size={13} />
                  ) : status === "changed" ? (
                    <Edit3 size={13} />
                  ) : (
                    <span>!</span>
                  )}
                </span>
              </button>
            );
          })
        ) : (
          <div className="empty-list">
            <Search size={22} />
            <strong>No members found</strong>
            <p>Change the search or filter to see more records.</p>
          </div>
        )}
      </div>
      <div className="nav-footer">
        <span>Keyboard</span>
        <strong>N</strong>
        <small>next unresolved</small>
      </div>
    </aside>
  );
}

function ReviewTray({
  member,
  editing,
  setEditing,
  beginEdit,
  draft,
  setDraft,
  note,
  setNote,
  editError,
  saveEdit,
  resolveField,
  markUnresolved,
  nextUnresolved,
  citedPages,
  setViewPage,
}) {
  const missing = getMissingField(member);
  const status = memberStatus(member);
  const longitudinal = member.kind === "beam" ? "length" : "height";
  const reason = missing ? member[`${missing}_null_reason`] : null;
  const hasProfile = editing ? Boolean(draft.profile) : Boolean(member.profile);
  return (
    <section
      className={`review-tray ${editing ? "editing" : ""} ${hasProfile ? "has-profile" : ""}`}
    >
      <header className="tray-header">
        <div className="member-title">
          <h2>
            {member.kind === "beam" ? "Beam" : "Column"}{" "}
            {member.drawing_id || "Unlabelled"}
          </h2>
          <StatusBadge status={status} />
          <span>{member.level || "Level not established"}</span>
        </div>
        <div className="tray-actions">
          {editing ? (
            <>
              <button
                className="button secondary compact"
                onClick={() => setEditing(false)}
              >
                Cancel
              </button>
              <button className="button primary compact" onClick={saveEdit}>
                <Check size={15} />
                Save changes
              </button>
            </>
          ) : (
            <>
              <button className="button secondary compact" onClick={beginEdit}>
                <Edit3 size={15} />
                Edit member
              </button>
              <button
                className="button secondary compact next-button"
                onClick={nextUnresolved}
              >
                Next unresolved
                <SkipForward size={15} />
              </button>
            </>
          )}
        </div>
      </header>
      {editing && editError && (
        <div className="edit-error" role="alert">
          <AlertCircle size={15} />
          {editError}
        </div>
      )}
      {editing ? (
        <div className="edit-form">
          <label>
            ID
            <span className="read-only-field">{member.drawing_id || "—"}</span>
          </label>
          <label>
            Level
            <input
              value={draft.level}
              onChange={(e) => setDraft({ ...draft, level: e.target.value })}
            />
          </label>
          <label>
            Width ({member.unit || "mm"})
            {draft.profile ? (
              <span className="read-only-field">See profile stations</span>
            ) : (
              <input
                type="number"
                value={draft.width}
                onChange={(e) => setDraft({ ...draft, width: e.target.value })}
              />
            )}
          </label>
          <label>
            Depth ({member.unit || "mm"})
            {draft.profile ? (
              <span className="read-only-field">See profile stations</span>
            ) : (
              <input
                type="number"
                value={draft.depth}
                onChange={(e) => setDraft({ ...draft, depth: e.target.value })}
              />
            )}
          </label>
          <label>
            {longitudinal === "length" ? "Length" : "Height"} (
            {member.unit || "mm"})
            <input
              type="number"
              value={draft[longitudinal]}
              onChange={(e) =>
                setDraft({ ...draft, [longitudinal]: e.target.value })
              }
            />
          </label>
          <label className="wide-field">
            Location
            <input
              value={draft.location}
              onChange={(e) => setDraft({ ...draft, location: e.target.value })}
            />
          </label>
          <label className="wide-field">
            Optional change note
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Why was this value changed?"
            />
          </label>
          {member.kind === "beam" && (
            <div className="profile-edit-region">
              {draft.profile ? (
                <ProfileEditor
                  profile={draft.profile}
                  onChange={(profile) => setDraft({ ...draft, profile })}
                  unit={member.unit}
                  beamLength={draft.length}
                />
              ) : (
                <div className="add-profile-row">
                  <div>
                    <strong>Complex cross-section</strong>
                    <span>
                      Add exact stations when one rectangular width and depth
                      cannot represent this beam.
                    </span>
                    <label>
                      Profile assessment
                      <input
                        value={draft.profile_null_reason}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            profile_null_reason: e.target.value,
                          })
                        }
                        placeholder="Section/detail checked and conclusion"
                      />
                    </label>
                  </div>
                  <button
                    type="button"
                    className="button secondary compact"
                    onClick={() =>
                      setDraft({
                        ...draft,
                        profile: {
                          shape: "custom",
                          start_location: "",
                          stations: [
                            {
                              distance: 0,
                              width: null,
                              depth: null,
                              vertices: [
                                { x: "", y: "" },
                                { x: "", y: "" },
                                { x: "", y: "" },
                              ],
                            },
                          ],
                        },
                      })
                    }
                  >
                    <Plus size={15} />
                    Add profile
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="tray-content">
            <div className="member-facts">
              <Fact
                label="Width"
                value={member.width}
                original={member.original.width}
                unit={member.unit}
                fallback={member.profile ? "See profile" : undefined}
              />
              <Fact
                label="Depth"
                value={member.depth}
                original={member.original.depth}
                unit={member.unit}
                fallback={member.profile ? "See profile" : undefined}
              />
              <Fact
                label={longitudinal === "length" ? "Length" : "Height"}
                value={member[longitudinal]}
                original={member.original[longitudinal]}
                unit={member.unit}
              />
              {member.kind === "beam" && member.profile && (
                <Fact
                  label="Profile"
                  value={profileSummary(member.profile)}
                  original={profileSummary(member.original.profile)}
                  changed={
                    JSON.stringify(member.profile) !==
                    JSON.stringify(member.original.profile)
                  }
                />
              )}
              <Fact
                label="Location"
                value={member.location}
                original={member.original.location}
                wide
              />
            </div>
            <div className="review-question">
              {missing ? (
                <>
                  <div className="question-copy">
                    <span className="question-icon">
                      <MessageSquareText size={17} />
                    </span>
                    <div>
                      <strong>
                        What is the {missing} of{" "}
                        {member.drawing_id || "this member"}?
                      </strong>
                      <p>
                        {reason ||
                          "The second-pass extraction did not establish one exact value."}
                      </p>
                      {citedPages.length > 0 && (
                        <div className="citation-links">
                          {citedPages.map((page) => (
                            <button key={page} onClick={() => setViewPage(page)}>
                              Open cited page {page}
                              <ChevronRight size={13} />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="answer-row">
                    {missing === "depth" &&
                      member.kind === "beam" &&
                      SUGGESTIONS.map((value) => (
                        <button
                          key={value}
                          className="answer-button"
                          onClick={() => resolveField(value)}
                        >
                          {value}
                          {value === "Varies" ? "" : ` ${member.unit || "mm"}`}
                        </button>
                      ))}
                    <button
                      className="answer-button subtle"
                      onClick={() => markUnresolved("cannot-determine")}
                    >
                      Cannot determine
                    </button>
                    <button
                      className="text-button"
                      onClick={() => markUnresolved("skipped")}
                    >
                      Skip
                    </button>
                  </div>
                </>
              ) : (
                <div className="resolved-message">
                  <span>
                    <Check size={17} />
                  </span>
                  <div>
                    <strong>Member values are complete</strong>
                    <p>
                      {member.reviewNote ||
                        "No unresolved dimensions remain for this record."}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
          {member.kind === "beam" && member.profile && (
            <ProfileReview profile={member.profile} unit={member.unit} />
          )}
        </>
      )}
    </section>
  );
}

function ProfileReview({ profile, unit }) {
  return (
    <section className="profile-review" aria-labelledby="profile-review-title">
      <header>
        <div>
          <h3 id="profile-review-title">Cross-section profile</h3>
          <p>
            {profileLabel(profile.shape)} · station zero at{" "}
            {profile.start_location}
          </p>
        </div>
        <span className="profile-coordinate-note">
          Origin: lower-left · +x right · +y up
        </span>
      </header>
      <div className="profile-stations">
        {profile.stations.map((station, index) => (
          <article
            className="profile-station"
            key={`${station.distance}-${index}`}
          >
            <ProfileDiagram
              station={station}
              unit={unit}
              label={`Cross-section at station ${station.distance} ${unit || "units"}`}
            />
            <div className="profile-station-data">
              <strong>
                Station {station.distance} {unit || ""}
              </strong>
              {station.vertices ? (
                <span>{station.vertices.length} exact vertices</span>
              ) : (
                <span>
                  {station.width} × {station.depth} {unit || ""}
                </span>
              )}
              {station.vertices && (
                <ol aria-label="Ordered cross-section vertices">
                  {station.vertices.map((point, pointIndex) => (
                    <li key={`${point.x}-${point.y}-${pointIndex}`}>
                      ({point.x}, {point.y})
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ProfileDiagram({ station, unit, label }) {
  const points = station.vertices?.length
    ? station.vertices
    : Number(station.width) > 0 && Number(station.depth) > 0
      ? [
          { x: 0, y: 0 },
          { x: Number(station.width), y: 0 },
          { x: Number(station.width), y: Number(station.depth) },
          { x: 0, y: Number(station.depth) },
        ]
      : [];
  const numericPoints = points
    .map((point) => ({ x: Number(point.x), y: Number(point.y) }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
  if (numericPoints.length < 3)
    return <div className="profile-diagram empty">Preview unavailable</div>;

  const xs = numericPoints.map((point) => point.x);
  const ys = numericPoints.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(maxX - minX, 1);
  const height = Math.max(maxY - minY, 1);
  const padding = Math.max(width, height) * 0.12;
  const svgPoints = numericPoints
    .map((point) => `${point.x},${maxY - point.y + minY}`)
    .join(" ");
  return (
    <figure className="profile-diagram">
      <svg
        viewBox={`${minX - padding} ${minY - padding} ${width + padding * 2} ${height + padding * 2}`}
        role="img"
        aria-label={label}
        preserveAspectRatio="xMidYMid meet"
      >
        <polygon points={svgPoints} />
      </svg>
      <figcaption>
        {formatDimension(width)} × {formatDimension(height)} {unit || ""}{" "}
        envelope
      </figcaption>
    </figure>
  );
}

function ProfileEditor({ profile, onChange, unit, beamLength }) {
  const polygon = POLYGON_PROFILE_SHAPES.has(profile.shape);
  const updateStation = (stationIndex, patch) =>
    onChange({
      ...profile,
      stations: profile.stations.map((station, index) =>
        index === stationIndex ? { ...station, ...patch } : station,
      ),
    });
  const updateVertex = (stationIndex, vertexIndex, axis, value) => {
    const station = profile.stations[stationIndex];
    updateStation(stationIndex, {
      vertices: station.vertices.map((point, index) =>
        index === vertexIndex ? { ...point, [axis]: value } : point,
      ),
    });
  };
  const changeShape = (shape) =>
    onChange({
      ...profile,
      shape,
      stations: profile.stations.map((station) => ({
        ...station,
        width: POLYGON_PROFILE_SHAPES.has(shape) ? null : station.width ?? "",
        depth: POLYGON_PROFILE_SHAPES.has(shape) ? null : station.depth ?? "",
        vertices: POLYGON_PROFILE_SHAPES.has(shape)
          ? station.vertices || [
              { x: "", y: "" },
              { x: "", y: "" },
              { x: "", y: "" },
            ]
          : null,
      })),
    });

  return (
    <section className="profile-editor" aria-labelledby="profile-editor-title">
      <header>
        <div>
          <strong id="profile-editor-title">Complex cross-section</strong>
          <span>All coordinates use {unit || "the member unit"}.</span>
        </div>
        <button
          type="button"
          className="text-button"
          onClick={() => onChange(null)}
        >
          Remove profile
        </button>
      </header>
      <div className="profile-editor-basics">
        <label>
          Shape
          <select
            value={profile.shape}
            onChange={(e) => changeShape(e.target.value)}
          >
            {PROFILE_SHAPES.map((shape) => (
              <option key={shape} value={shape}>
                {profileLabel(shape)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Station-zero grid or support
          <input
            value={profile.start_location}
            onChange={(e) =>
              onChange({ ...profile, start_location: e.target.value })
            }
            placeholder="e.g. Grid 3 support centreline"
          />
        </label>
        <span className="profile-length-note">
          Beam length: {beamLength || "unresolved"} {unit || ""}
        </span>
      </div>
      <div className="profile-editor-stations">
        {profile.stations.map((station, stationIndex) => (
          <fieldset key={stationIndex}>
            <legend>Station {stationIndex + 1}</legend>
            <label>
              Distance ({unit || "unit"})
              <input
                type="number"
                min="0"
                value={station.distance}
                onChange={(e) =>
                  updateStation(stationIndex, { distance: e.target.value })
                }
              />
            </label>
            {polygon ? (
              <div className="vertex-editor">
                <div className="vertex-heading">
                  <span>Ordered vertices</span>
                  <span>Lower-left origin; +x right, +y up</span>
                </div>
                {station.vertices.map((point, vertexIndex) => (
                  <div className="vertex-row" key={vertexIndex}>
                    <strong>{vertexIndex + 1}</strong>
                    <label>
                      x
                      <input
                        type="number"
                        min="0"
                        value={point.x}
                        onChange={(e) =>
                          updateVertex(
                            stationIndex,
                            vertexIndex,
                            "x",
                            e.target.value,
                          )
                        }
                      />
                    </label>
                    <label>
                      y
                      <input
                        type="number"
                        min="0"
                        value={point.y}
                        onChange={(e) =>
                          updateVertex(
                            stationIndex,
                            vertexIndex,
                            "y",
                            e.target.value,
                          )
                        }
                      />
                    </label>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={`Remove vertex ${vertexIndex + 1}`}
                      disabled={station.vertices.length <= 3}
                      onClick={() =>
                        updateStation(stationIndex, {
                          vertices: station.vertices.filter(
                            (_, index) => index !== vertexIndex,
                          ),
                        })
                      }
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className="text-button"
                  onClick={() =>
                    updateStation(stationIndex, {
                      vertices: [...station.vertices, { x: "", y: "" }],
                    })
                  }
                >
                  <Plus size={14} /> Add vertex
                </button>
              </div>
            ) : (
              <div className="station-dimensions">
                <label>
                  Width ({unit || "unit"})
                  <input
                    type="number"
                    min="0"
                    value={station.width ?? ""}
                    onChange={(e) =>
                      updateStation(stationIndex, { width: e.target.value })
                    }
                  />
                </label>
                <label>
                  Depth ({unit || "unit"})
                  <input
                    type="number"
                    min="0"
                    value={station.depth ?? ""}
                    onChange={(e) =>
                      updateStation(stationIndex, { depth: e.target.value })
                    }
                  />
                </label>
              </div>
            )}
            <ProfileDiagram
              station={station}
              unit={unit}
              label={`Draft cross-section at station ${station.distance}`}
            />
            <button
              type="button"
              className="text-button remove-station"
              disabled={profile.stations.length <= 1}
              onClick={() =>
                onChange({
                  ...profile,
                  stations: profile.stations.filter(
                    (_, index) => index !== stationIndex,
                  ),
                })
              }
            >
              Remove station
            </button>
          </fieldset>
        ))}
      </div>
      <button
        type="button"
        className="button secondary compact add-station"
        onClick={() =>
          onChange({
            ...profile,
            stations: [
              ...profile.stations,
              {
                distance: "",
                width: polygon ? null : "",
                depth: polygon ? null : "",
                vertices: polygon
                  ? [
                      { x: "", y: "" },
                      { x: "", y: "" },
                      { x: "", y: "" },
                    ]
                  : null,
              },
            ],
          })
        }
      >
        <Plus size={14} /> Add station
      </button>
    </section>
  );
}

function Fact({ label, value, original, unit, wide, fallback, changed }) {
  const wasChanged = changed ?? value !== original;
  return (
    <div className={`fact ${wide ? "wide" : ""}`}>
      <span>{label}</span>
      <strong>
        {value ?? fallback ?? "—"}
        {typeof value === "number" ? ` ${unit || ""}` : ""}
      </strong>
      {wasChanged && <small>Original: {original ?? "unresolved"}</small>}
    </div>
  );
}

function StatusBadge({ status }) {
  const labels = {
    confirmed: "Confirmed",
    unresolved: "Unresolved",
    changed: "Changed",
    skipped: "Skipped",
    "cannot-determine": "Cannot determine",
  };
  return (
    <span className={`status-badge ${status}`}>
      {status === "confirmed" ? (
        <Check size={12} />
      ) : status === "changed" ? (
        <Edit3 size={12} />
      ) : (
        <AlertCircle size={12} />
      )}
      {labels[status] || status}
    </span>
  );
}

function ExportWarning({ warning, cancel, proceed }) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <section
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-title"
      >
        <button className="dialog-close" onClick={cancel} aria-label="Close">
          <X size={18} />
        </button>
        <span className="warning-icon">
          <AlertCircle size={22} />
        </span>
        <h2 id="export-title">Export with unresolved members?</h2>
        <p>
          {warning.unresolvedCount} members still have unresolved, skipped, or
          indeterminate values. They will remain explicit in the{" "}
          {warning.format.toUpperCase()} export.
        </p>
        <div className="dialog-summary">
          <span>
            <strong>{warning.unresolvedCount}</strong> unresolved
          </span>
          <span>
            <strong>0</strong> values converted to zero
          </span>
        </div>
        <div className="dialog-actions">
          <button className="button secondary" onClick={cancel}>
            Keep reviewing
          </button>
          <button className="button primary" onClick={proceed}>
            Export anyway
          </button>
        </div>
      </section>
    </div>
  );
}

export default App;
