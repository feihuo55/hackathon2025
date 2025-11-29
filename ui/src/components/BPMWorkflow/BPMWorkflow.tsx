import { ArrowRight, ArrowDown, Circle, Play, CheckCircle2, Database, Users, FileText, Settings, Send } from 'lucide-react';
import type { SIPOCDocument } from '../../types';
import './BPMWorkflow.css';

interface BPMWorkflowProps {
  sipoc: SIPOCDocument;
  title?: string;
}

interface WorkflowNode {
  id: string;
  type: 'start' | 'end' | 'task' | 'gateway';
  label: string;
  sublabel?: string;
}

export function BPMWorkflow({ sipoc, title = "BPMN 2.0 Workflow" }: BPMWorkflowProps) {
  // Create workflow nodes from SIPOC process steps
  const createWorkflowNodes = (): WorkflowNode[] => {
    const nodes: WorkflowNode[] = [];

    // Start event
    nodes.push({
      id: 'start',
      type: 'start',
      label: 'Start',
      sublabel: 'Process Initiated'
    });

    // Add each process step as a task
    sipoc.process.forEach((step, index) => {
      // Clean up step text (remove numbering like "1. ")
      const cleanStep = step.replace(/^\d+\.\s*/, '');

      nodes.push({
        id: `task-${index + 1}`,
        type: 'task',
        label: cleanStep,
        sublabel: `Step ${index + 1}`
      });

      // Add validation gateway after validation steps
      if (cleanStep.toLowerCase().includes('validate') || cleanStep.toLowerCase().includes('verify')) {
        nodes.push({
          id: `gateway-${index + 1}`,
          type: 'gateway',
          label: 'Valid?',
          sublabel: 'Decision'
        });
      }
    });

    // End event
    nodes.push({
      id: 'end',
      type: 'end',
      label: 'End',
      sublabel: 'Process Complete'
    });

    return nodes;
  };

  const nodes = createWorkflowNodes();

  // Get icon for node based on content
  const getNodeIcon = (node: WorkflowNode) => {
    if (node.type === 'start') return <Play size={16} />;
    if (node.type === 'end') return <CheckCircle2 size={16} />;
    if (node.type === 'gateway') return null;

    const label = node.label.toLowerCase();
    if (label.includes('retrieve') || label.includes('get') || label.includes('fetch')) return <Database size={16} />;
    if (label.includes('validate') || label.includes('verify') || label.includes('check')) return <CheckCircle2 size={16} />;
    if (label.includes('calculate') || label.includes('process')) return <Settings size={16} />;
    if (label.includes('execute') || label.includes('distribute')) return <Send size={16} />;
    if (label.includes('update') || label.includes('record')) return <Database size={16} />;
    if (label.includes('generate') || label.includes('report')) return <FileText size={16} />;
    if (label.includes('notify') || label.includes('stakeholder')) return <Users size={16} />;
    return <Settings size={16} />;
  };

  const renderNode = (node: WorkflowNode, index: number) => {
    return (
      <div key={node.id} className="bpm-node-container">
        <div className={`bpm-node bpm-node-${node.type}`}>
          {node.type === 'start' && (
            <div className="bpm-event bpm-start-event">
              <Play size={18} />
            </div>
          )}
          {node.type === 'end' && (
            <div className="bpm-event bpm-end-event">
              <Circle size={18} fill="currentColor" />
            </div>
          )}
          {node.type === 'gateway' && (
            <div className="bpm-gateway">
              <span>?</span>
            </div>
          )}
          {node.type === 'task' && (
            <div className="bpm-task">
              <div className="bpm-task-icon">{getNodeIcon(node)}</div>
              <div className="bpm-task-content">
                <span className="bpm-task-label">{node.label}</span>
              </div>
            </div>
          )}
        </div>
        {node.sublabel && node.type !== 'task' && (
          <span className="bpm-node-sublabel">{node.sublabel}</span>
        )}
      </div>
    );
  };

  const renderConnector = (index: number, isVertical: boolean = false) => {
    if (isVertical) {
      return (
        <div className="bpm-connector bpm-connector-vertical">
          <div className="bpm-connector-line-v"></div>
          <ArrowDown size={14} className="bpm-connector-arrow" />
        </div>
      );
    }
    return (
      <div className="bpm-connector bpm-connector-horizontal">
        <div className="bpm-connector-line"></div>
        <ArrowRight size={14} className="bpm-connector-arrow" />
      </div>
    );
  };

  return (
    <div className="bpm-workflow-container">
      {/* Header */}
      <div className="bpm-workflow-header">
        <div className="bpm-workflow-title">
          <Settings size={20} />
          <span>{title}</span>
        </div>
        <div className="bpm-workflow-badge">BPMN 2.0</div>
      </div>

      {/* Pool */}
      <div className="bpm-pool">
        <div className="bpm-pool-header">
          <span>Fund Dividend Distribution Process</span>
        </div>

        {/* Swimlane */}
        <div className="bpm-swimlane">
          <div className="bpm-swimlane-header">
            <span className="bpm-swimlane-role">Custody Bank System</span>
          </div>

          {/* Flow */}
          <div className="bpm-flow">
            {nodes.map((node, index) => (
              <div key={node.id} className="bpm-flow-item">
                {renderNode(node, index)}
                {index < nodes.length - 1 && renderConnector(index)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SIPOC Summary */}
      <div className="bpm-sipoc-summary">
        <div className="bpm-sipoc-section">
          <div className="bpm-sipoc-label">Suppliers</div>
          <div className="bpm-sipoc-items">
            {sipoc.suppliers.map((s, i) => (
              <span key={i} className="bpm-sipoc-item supplier">{s}</span>
            ))}
          </div>
        </div>
        <div className="bpm-sipoc-section">
          <div className="bpm-sipoc-label">Inputs</div>
          <div className="bpm-sipoc-items">
            {sipoc.inputs.map((s, i) => (
              <span key={i} className="bpm-sipoc-item input">{s}</span>
            ))}
          </div>
        </div>
        <div className="bpm-sipoc-section">
          <div className="bpm-sipoc-label">Outputs</div>
          <div className="bpm-sipoc-items">
            {sipoc.outputs.map((s, i) => (
              <span key={i} className="bpm-sipoc-item output">{s}</span>
            ))}
          </div>
        </div>
        <div className="bpm-sipoc-section">
          <div className="bpm-sipoc-label">Customers</div>
          <div className="bpm-sipoc-items">
            {sipoc.customers.map((s, i) => (
              <span key={i} className="bpm-sipoc-item customer">{s}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bpm-legend">
        <div className="bpm-legend-item">
          <div className="bpm-legend-icon bpm-legend-start"><Play size={10} /></div>
          <span>Start Event</span>
        </div>
        <div className="bpm-legend-item">
          <div className="bpm-legend-icon bpm-legend-end"><Circle size={10} fill="currentColor" /></div>
          <span>End Event</span>
        </div>
        <div className="bpm-legend-item">
          <div className="bpm-legend-icon bpm-legend-task"></div>
          <span>Task</span>
        </div>
        <div className="bpm-legend-item">
          <div className="bpm-legend-icon bpm-legend-gateway"></div>
          <span>Gateway</span>
        </div>
      </div>
    </div>
  );
}
