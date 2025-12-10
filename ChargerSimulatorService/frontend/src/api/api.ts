import axios from 'axios';
import { SimulatorConfig, Session } from '../types';

const api = axios.create({
  baseURL: '/api',
});

export const getConfig = async (): Promise<SimulatorConfig> => {
  const response = await api.get<SimulatorConfig>('/config');
  return response.data;
};

export const updateConfig = async (config: SimulatorConfig): Promise<SimulatorConfig> => {
  const response = await api.put<SimulatorConfig>('/config', config);
  return response.data;
};

export const getSessions = async (): Promise<Session[]> => {
  const response = await api.get<Session[]>('/sessions');
  return response.data;
};
