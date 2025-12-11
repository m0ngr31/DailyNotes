import { Requests } from './requests';

export interface IUploadResponse {
  url: string;
  path: string;
  filename: string;
}

export const UploadService = {
  uploadImage: async (file: File): Promise<IUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await Requests.upload('/upload', formData);
    return res.data as IUploadResponse;
  },
};
